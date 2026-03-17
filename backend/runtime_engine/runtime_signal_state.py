from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from runtime_engine.runtime_telemetry import runtime_telemetry
from services.io_mapping_engine import io_mapping_engine


@dataclass
class TagDefinition:
    tag: str
    io_type: str
    data_type: str
    is_input: bool


class RuntimeSignalState:
    """In-memory runtime signal values + input force overrides per project."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._tag_defs: dict[str, dict[str, TagDefinition]] = {}
        self._current_values: dict[str, dict[str, Any]] = {}
        self._forced_values: dict[str, dict[str, dict[str, Any]]] = {}

    @staticmethod
    def _infer_data_type(io_type: str, signal_type: str | None = None) -> str:
        normalized_io = io_type.upper()
        normalized_signal = (signal_type or "").strip().lower()

        if normalized_signal in {"bool", "boolean", "digital", "discrete"}:
            return "BOOL"
        if normalized_signal in {"int", "integer"}:
            return "INT"
        if normalized_signal in {"float", "double", "real", "analog", "pressure", "flow", "level", "temperature"}:
            return "REAL"

        if normalized_io in {"DI", "DO"}:
            return "BOOL"
        if normalized_io in {"AI", "AO"}:
            return "REAL"
        return "REAL"

    @staticmethod
    def _default_value(data_type: str) -> Any:
        if data_type == "BOOL":
            return False
        if data_type == "INT":
            return 0
        if data_type == "STRING":
            return ""
        return 0.0

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in {0, 1}:
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        raise ValueError("Invalid BOOL value. Use true/false.")

    def _coerce_typed_value(self, value: Any, expected_type: str) -> Any:
        if expected_type == "BOOL":
            return self._coerce_bool(value)
        if expected_type == "INT":
            if isinstance(value, bool):
                raise ValueError("Invalid INT value.")
            if isinstance(value, int):
                return value
            if isinstance(value, float) and value.is_integer():
                return int(value)
            if isinstance(value, str) and value.strip().lstrip("-").isdigit():
                return int(value.strip())
            raise ValueError("Invalid INT value.")
        if expected_type == "STRING":
            return str(value)

        if isinstance(value, bool):
            raise ValueError("Invalid REAL value.")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError as exc:
                raise ValueError("Invalid REAL value.") from exc
        raise ValueError("Invalid REAL value.")

    @staticmethod
    def _is_input_io(io_type: str) -> bool:
        return io_type.upper() in {"AI", "DI"}

    def _load_catalog_from_latest_io(self, project_id: str) -> list[dict[str, Any]]:
        latest = io_mapping_engine.get_latest_io_mapping(project_id)
        if not latest:
            return []
        return list(latest.get("rows", []))

    def ensure_project(self, project_id: str, io_rows: list[dict[str, Any]] | None = None) -> int:
        with self._lock:
            if project_id in self._tag_defs:
                return len(self._tag_defs[project_id])

            source_rows = io_rows if io_rows is not None else self._load_catalog_from_latest_io(project_id)
            tag_defs: dict[str, TagDefinition] = {}
            values: dict[str, Any] = {}

            for row in source_rows:
                tag = str(row.get("tag") or "").strip()
                io_type = str(row.get("io_type") or "").upper().strip()
                if not tag:
                    continue

                signal_type = str(row.get("signal_type") or "").strip()
                st_type = str(row.get("st_type") or row.get("data_type") or "").upper().strip()

                if io_type in {"AI", "AO", "DI", "DO"}:
                    data_type = self._infer_data_type(io_type, signal_type)
                    is_input = self._is_input_io(io_type)
                else:
                    data_type = st_type if st_type in {"BOOL", "INT", "REAL", "STRING"} else self._infer_data_type(io_type or "AI", signal_type)
                    io_type = io_type or "VIRTUAL"
                    is_input = bool(row.get("is_input", True))

                tag_defs[tag] = TagDefinition(
                    tag=tag,
                    io_type=io_type,
                    data_type=data_type,
                    is_input=is_input,
                )
                values[tag] = self._default_value(data_type)

            self._tag_defs[project_id] = tag_defs
            self._current_values[project_id] = values
            self._forced_values[project_id] = {}
            return len(tag_defs)

    def _recompute_derived_tags(self, project_id: str) -> None:
        tag_defs = self._tag_defs.get(project_id, {})
        current = self._current_values.get(project_id, {})
        forced = self._forced_values.get(project_id, {})

        for tag, value in list(current.items()):
            if not tag.endswith("_CMD"):
                continue
            status_tag = f"{tag[:-4]}_STATUS"
            if status_tag in current and status_tag not in forced:
                current[status_tag] = bool(value)

        if "PLANT_FAULT_ACTIVE" in current and "PLANT_FAULT_ACTIVE" not in forced:
            fault_values: list[bool] = []
            for tag_name, tag_def in tag_defs.items():
                if tag_name.endswith("_FAULT") and tag_name != "PLANT_FAULT_ACTIVE" and tag_def.data_type == "BOOL":
                    fault_values.append(bool(current.get(tag_name, False)))
            current["PLANT_FAULT_ACTIVE"] = any(fault_values)

    def _sync_runtime_telemetry(self, project_id: str) -> None:
        current = self._current_values.get(project_id, {})
        forced = self._forced_values.get(project_id, {})
        runtime_telemetry.update_tags(current)
        runtime_telemetry.update_tag("FORCED_INPUT_COUNT", len(forced))
        runtime_telemetry.update_tag("FORCED_INPUT_TAGS", sorted(forced.keys()))

    def apply_force(self, project_id: str, tag: str, value: Any, declared_type: str | None = None) -> dict[str, Any]:
        with self._lock:
            if project_id not in self._tag_defs:
                self.ensure_project(project_id)

            if project_id not in self._tag_defs or not self._tag_defs[project_id]:
                raise ValueError("No runtime tag catalog available for this project.")

            tag_defs = self._tag_defs[project_id]
            if tag not in tag_defs:
                raise ValueError(f"Unknown tag `{tag}`.")

            tag_def = tag_defs[tag]
            if not tag_def.is_input:
                raise ValueError(f"Tag `{tag}` is not an input tag and cannot be forced.")

            if declared_type and declared_type.upper() != tag_def.data_type:
                raise ValueError(f"Type mismatch for `{tag}`: expected {tag_def.data_type}, got {declared_type.upper()}.")

            coerced = self._coerce_typed_value(value, tag_def.data_type)
            forced_at = self._now_iso()
            self._forced_values[project_id][tag] = {
                "tag": tag,
                "value": coerced,
                "type": tag_def.data_type,
                "forced": True,
                "forced_at": forced_at,
            }
            self._current_values[project_id][tag] = coerced
            self._recompute_derived_tags(project_id)
            self._sync_runtime_telemetry(project_id)

            return {
                "tag": tag,
                "value": coerced,
                "type": tag_def.data_type,
                "forced": True,
                "forced_at": forced_at,
            }

    def clear_force(self, project_id: str, tag: str) -> dict[str, Any]:
        with self._lock:
            if project_id not in self._tag_defs:
                self.ensure_project(project_id)

            tag_defs = self._tag_defs.get(project_id, {})
            if tag not in tag_defs:
                raise ValueError(f"Unknown tag `{tag}`.")

            tag_def = tag_defs[tag]
            self._forced_values.get(project_id, {}).pop(tag, None)
            self._current_values[project_id][tag] = self._default_value(tag_def.data_type)
            self._recompute_derived_tags(project_id)
            self._sync_runtime_telemetry(project_id)

            return {
                "tag": tag,
                "value": self._current_values[project_id][tag],
                "type": tag_def.data_type,
                "forced": False,
                "forced_at": None,
            }

    def get_forced_inputs(self, project_id: str) -> list[dict[str, Any]]:
        with self._lock:
            if project_id not in self._tag_defs:
                self.ensure_project(project_id)
            return list(self._forced_values.get(project_id, {}).values())

    def get_input_catalog(self, project_id: str) -> list[dict[str, Any]]:
        with self._lock:
            if project_id not in self._tag_defs:
                self.ensure_project(project_id)

            current = self._current_values.get(project_id, {})
            forced = self._forced_values.get(project_id, {})
            rows: list[dict[str, Any]] = []
            for tag_name, tag_def in sorted(self._tag_defs.get(project_id, {}).items()):
                if not tag_def.is_input:
                    continue
                forced_state = forced.get(tag_name)
                rows.append(
                    {
                        "tag": tag_name,
                        "io_type": tag_def.io_type,
                        "type": tag_def.data_type,
                        "current_value": current.get(tag_name),
                        "forced": forced_state is not None,
                        "forced_at": forced_state.get("forced_at") if forced_state else None,
                    }
                )
            return rows

    def sync_project(self, project_id: str, io_rows: list[dict[str, Any]] | None = None) -> None:
        self.ensure_project(project_id, io_rows=io_rows)
        with self._lock:
            self._recompute_derived_tags(project_id)
            self._sync_runtime_telemetry(project_id)

    def get_project_snapshot(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            if project_id not in self._tag_defs:
                self.ensure_project(project_id)
            return {
                "current_values": dict(self._current_values.get(project_id, {})),
                "forced_inputs": list(self._forced_values.get(project_id, {}).values()),
            }

    def apply_evaluated_values(self, project_id: str, evaluated_values: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if project_id not in self._tag_defs:
                self.ensure_project(project_id)
            target = self._current_values.setdefault(project_id, {})
            target.update(evaluated_values)
            self._recompute_derived_tags(project_id)
            self._sync_runtime_telemetry(project_id)
            return dict(target)


runtime_signal_state = RuntimeSignalState()
