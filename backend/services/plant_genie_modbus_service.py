from __future__ import annotations

import struct
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    from pymodbus.client import ModbusTcpClient  # type: ignore
except Exception:  # pragma: no cover
    ModbusTcpClient = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ModbusConnectorSample:
    tag: str
    value: Any
    observed_at: datetime
    quality: str | None = None
    engineering_units: str | None = None


@dataclass(frozen=True)
class _MappingWindow:
    register_type: str
    start: int
    count: int
    mappings: tuple[dict[str, Any], ...]


class PlantGenieModbusService:
    def create_client(self, config: Mapping[str, Any]) -> Any:
        if ModbusTcpClient is None:
            raise RuntimeError("Modbus TCP connector is unavailable on the server (missing pymodbus).")
        normalized = self._normalize_connector_config(config)
        timeout_seconds = max(float(normalized["timeout_ms"]) / 1000.0, 0.1)
        return ModbusTcpClient(
            host=str(normalized["host"]),
            port=int(normalized["port"]),
            timeout=timeout_seconds,
        )

    def close_client(self, client: Any) -> None:
        try:
            client.close()
        except Exception:
            pass

    def ensure_connected(self, client: Any) -> None:
        if getattr(client, "connected", False):
            return
        if not bool(client.connect()):
            raise RuntimeError("Unable to connect to Modbus TCP endpoint.")

    @contextmanager
    def connection(self, config: Mapping[str, Any]) -> Iterator[Any]:
        client = self.create_client(config)
        try:
            self.ensure_connected(client)
            yield client
        finally:
            self.close_client(client)

    def test_connection(self, config: Mapping[str, Any]) -> tuple[bool, str]:
        normalized = self._normalize_connector_config(config)
        try:
            with self.connection(normalized) as client:
                mappings = list(normalized["tag_mappings"])
                if mappings:
                    self._read_windows(client, normalized, [mappings[0]])
            return True, "Modbus TCP connection succeeded."
        except Exception as exc:
            return False, str(exc)

    def preview_data(self, config: Mapping[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_connector_config(config)
        with self.connection(normalized) as client:
            samples = self.fetch_runtime_samples(normalized, client=client)
        rows = [
            {
                "internal_tag": sample.tag,
                "value": self._serialize_value(sample.value),
                "quality": sample.quality,
                "engineering_units": sample.engineering_units,
                "observed_at": sample.observed_at.isoformat(),
            }
            for sample in samples
        ]
        return {
            "columns": ["internal_tag", "value", "quality", "engineering_units", "observed_at"],
            "rows": rows,
            "row_count": len(rows),
        }

    def fetch_runtime_samples(self, config: Mapping[str, Any], *, client: Any) -> list[ModbusConnectorSample]:
        normalized = self._normalize_connector_config(config)
        self.ensure_connected(client)
        return self._read_windows(client, normalized, normalized["tag_mappings"])

    def _read_windows(self, client: Any, config: Mapping[str, Any], mappings: Iterable[dict[str, Any]]) -> list[ModbusConnectorSample]:
        windows = self._build_windows(config, list(mappings))
        observed_at = _utc_now()
        samples: list[ModbusConnectorSample] = []
        for window in windows:
            response = self._execute_with_retries(
                client,
                config,
                lambda: self._read_window(client, config, window),
            )
            for mapping in window.mappings:
                samples.append(self._decode_mapping(mapping, response, window.start, observed_at))
        return samples

    def _execute_with_retries(self, client: Any, config: Mapping[str, Any], operation) -> Any:  # type: ignore[no-untyped-def]
        last_error: Exception | None = None
        attempts = int(config.get("retry_attempts") or 0) + 1
        for _ in range(max(attempts, 1)):
            try:
                self.ensure_connected(client)
                return operation()
            except Exception as exc:
                last_error = exc
                if bool(config.get("auto_reconnect", True)):
                    self.close_client(client)
                    self.ensure_connected(client)
        raise RuntimeError(str(last_error) if last_error is not None else "Modbus read failed.")

    def _read_window(self, client: Any, config: Mapping[str, Any], window: _MappingWindow) -> Any:
        unit_id = int(config["unit_id"])
        if window.register_type == "coil":
            response = client.read_coils(address=window.start, count=window.count, slave=unit_id)
        elif window.register_type == "discrete_input":
            response = client.read_discrete_inputs(address=window.start, count=window.count, slave=unit_id)
        elif window.register_type == "holding_register":
            response = client.read_holding_registers(address=window.start, count=window.count, slave=unit_id)
        else:
            response = client.read_input_registers(address=window.start, count=window.count, slave=unit_id)
        if response is None or response.isError():
            raise RuntimeError(f"Modbus {window.register_type} read failed for address {window.start}.")
        return response

    def _decode_mapping(self, mapping: Mapping[str, Any], response: Any, window_start: int, observed_at: datetime) -> ModbusConnectorSample:
        register_type = str(mapping["register_type"])
        address = int(mapping["address"])
        quantity = int(mapping["quantity"])
        data_type = str(mapping["data_type"])
        offset = address - window_start

        if register_type in {"coil", "discrete_input"}:
            bits = [bool(bit) for bit in list(getattr(response, "bits", []))[offset: offset + quantity]]
            raw_value: Any = bits[0] if quantity == 1 else bits
        else:
            expected_registers = self._required_register_count(data_type, quantity)
            registers = [int(value) & 0xFFFF for value in list(getattr(response, "registers", []))[offset: offset + expected_registers]]
            if len(registers) < expected_registers:
                raise RuntimeError(f"Insufficient Modbus registers returned for tag {mapping['internal_tag']}.")
            raw_value = self._decode_registers(
                registers=registers,
                data_type=data_type,
                endianness=str(mapping["endianness"]),
                word_swap=bool(mapping["word_swap"]),
                quantity=quantity,
            )

        value = self._apply_scaling(raw_value, float(mapping["multiplier"]), float(mapping["offset"]))
        return ModbusConnectorSample(
            tag=str(mapping["internal_tag"]),
            value=value,
            observed_at=observed_at,
            quality="good",
            engineering_units=str(mapping.get("engineering_units") or "").strip() or None,
        )

    def _decode_registers(self, *, registers: list[int], data_type: str, endianness: str, word_swap: bool, quantity: int) -> Any:
        raw = b"".join(int(register).to_bytes(2, byteorder="big", signed=False) for register in registers)
        if word_swap and len(registers) > 1:
            words = [raw[index:index + 2] for index in range(0, len(raw), 2)]
            raw = b"".join(reversed(words))
        byte_order = "little" if endianness == "little" else "big"

        if data_type == "string":
            return raw[: max(quantity, 1) * 2].decode("utf-8", errors="replace").rstrip("\x00 ")
        if data_type == "bool":
            return bool(int.from_bytes(raw[:2], byteorder=byte_order, signed=False))
        if data_type == "uint16":
            return int.from_bytes(raw[:2], byteorder=byte_order, signed=False)
        if data_type == "int16":
            return int.from_bytes(raw[:2], byteorder=byte_order, signed=True)
        if data_type == "uint32":
            return int.from_bytes(raw[:4], byteorder=byte_order, signed=False)
        if data_type == "int32":
            return int.from_bytes(raw[:4], byteorder=byte_order, signed=True)
        if data_type == "uint64":
            return int.from_bytes(raw[:8], byteorder=byte_order, signed=False)
        if data_type == "int64":
            return int.from_bytes(raw[:8], byteorder=byte_order, signed=True)
        if data_type == "float32":
            format_code = "<f" if byte_order == "little" else ">f"
            return struct.unpack(format_code, raw[:4])[0]
        if data_type == "float64":
            format_code = "<d" if byte_order == "little" else ">d"
            return struct.unpack(format_code, raw[:8])[0]
        raise RuntimeError(f"Unsupported Modbus data type: {data_type}")

    def _build_windows(self, config: Mapping[str, Any], mappings: list[dict[str, Any]]) -> list[_MappingWindow]:
        if not mappings:
            return []
        max_request = int(config["max_registers_per_request"])
        batch_read = bool(config.get("batch_read"))
        windows: list[_MappingWindow] = []
        mappings_by_type: dict[str, list[dict[str, Any]]] = {}
        for mapping in mappings:
            mappings_by_type.setdefault(str(mapping["register_type"]), []).append(mapping)

        for register_type, type_mappings in mappings_by_type.items():
            ordered = sorted(type_mappings, key=lambda item: int(item["address"]))
            if not batch_read:
                for mapping in ordered:
                    span = self._mapping_span(mapping)
                    windows.append(
                        _MappingWindow(
                            register_type=register_type,
                            start=int(mapping["address"]),
                            count=span,
                            mappings=(mapping,),
                        )
                    )
                continue

            current_start = int(ordered[0]["address"])
            current_end = current_start + self._mapping_span(ordered[0])
            current_mappings: list[dict[str, Any]] = [ordered[0]]
            for mapping in ordered[1:]:
                mapping_start = int(mapping["address"])
                mapping_end = mapping_start + self._mapping_span(mapping)
                proposed_count = mapping_end - current_start
                if mapping_start <= current_end and proposed_count <= max_request:
                    current_end = max(current_end, mapping_end)
                    current_mappings.append(mapping)
                    continue
                windows.append(
                    _MappingWindow(
                        register_type=register_type,
                        start=current_start,
                        count=current_end - current_start,
                        mappings=tuple(current_mappings),
                    )
                )
                current_start = mapping_start
                current_end = mapping_end
                current_mappings = [mapping]
            windows.append(
                _MappingWindow(
                    register_type=register_type,
                    start=current_start,
                    count=current_end - current_start,
                    mappings=tuple(current_mappings),
                )
            )
        return windows

    def _mapping_span(self, mapping: Mapping[str, Any]) -> int:
        register_type = str(mapping["register_type"])
        if register_type in {"coil", "discrete_input"}:
            return max(int(mapping["quantity"]), 1)
        return self._required_register_count(str(mapping["data_type"]), int(mapping["quantity"]))

    @staticmethod
    def _required_register_count(data_type: str, quantity: int) -> int:
        if data_type in {"bool", "uint16", "int16"}:
            return 1
        if data_type in {"uint32", "int32", "float32"}:
            return 2
        if data_type in {"uint64", "int64", "float64"}:
            return 4
        if data_type == "string":
            return max(quantity, 1)
        raise RuntimeError(f"Unsupported Modbus data type: {data_type}")

    def _normalize_connector_config(self, config: Mapping[str, Any]) -> dict[str, Any]:
        host = str(config.get("host") or "").strip()
        if not host:
            raise ValueError("config.host is required")
        tag_mappings = self._normalize_tag_mappings(config.get("tag_mappings") or config.get("tagMappings") or [])
        return {
            "host": host,
            "port": int(config.get("port") or 502),
            "unit_id": int(config.get("unit_id") or config.get("unitId") or 1),
            "timeout_ms": int(config.get("timeout_ms") or config.get("timeoutMs") or 5000),
            "retry_attempts": int(config.get("retry_attempts") or config.get("retryAttempts") or 2),
            "auto_reconnect": bool(config.get("auto_reconnect", True)),
            "batch_read": bool(config.get("batch_read")),
            "max_registers_per_request": int(config.get("max_registers_per_request") or config.get("maxRegistersPerRequest") or 120),
            "enable_write": bool(config.get("enable_write")),
            "write_function_code": str(config.get("write_function_code") or config.get("writeFunctionCode") or "fc6").lower(),
            "confirm_before_write": bool(config.get("confirm_before_write")),
            "write_rate_limit_ms": int(config.get("write_rate_limit_ms") or config.get("writeRateLimitMs") or 1000),
            "tag_mappings": tag_mappings,
        }

    def _normalize_tag_mappings(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError("config.tag_mappings must be a list")
        normalized: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError("config.tag_mappings items must be objects")
            normalized.append(
                {
                    "register_type": str(item.get("register_type") or item.get("registerType") or "").strip().lower(),
                    "address": int(item.get("address") or 0),
                    "quantity": int(item.get("quantity") or 1),
                    "data_type": str(item.get("data_type") or item.get("dataType") or "").strip().lower(),
                    "endianness": str(item.get("endianness") or "big").strip().lower() or "big",
                    "word_swap": bool(item.get("word_swap") or item.get("wordSwap")),
                    "internal_tag": str(item.get("internal_tag") or item.get("internalTag") or "").strip(),
                    "multiplier": float(item.get("multiplier") or 1.0),
                    "offset": float(item.get("offset") or 0.0),
                    "engineering_units": str(item.get("engineering_units") or item.get("engineeringUnits") or "").strip() or None,
                    "writable": bool(item.get("writable")),
                }
            )
        if not normalized:
            raise ValueError("config.tag_mappings must include at least one register mapping")
        return normalized

    @staticmethod
    def _apply_scaling(value: Any, multiplier: float, offset: float) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, list):
            return [PlantGenieModbusService._apply_scaling(item, multiplier, offset) for item in value]
        if isinstance(value, (int, float)):
            return (value * multiplier) + offset
        return value

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value


plant_genie_modbus_service = PlantGenieModbusService()