from __future__ import annotations

import asyncio
import json
import logging
import ssl
import tempfile
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from db.influx import influx_client
from services.control_loop_store import control_loop_store
from services.plant_genie_plant_data_service import (
    PlantGeniePlantDataConnectorRecord,
    plant_genie_plant_data_connector_service,
)
from services.plant_genie_historian_service import plant_genie_historian_service
from services.plant_genie_modbus_service import plant_genie_modbus_service
from services.uns_core import uns_core

try:
    from asyncua import Client as AsyncUAClient, ua  # type: ignore
except Exception:  # pragma: no cover
    AsyncUAClient = None
    ua = None

try:
    import paho.mqtt.client as mqtt  # type: ignore
except Exception:  # pragma: no cover
    mqtt = None

from services.plant_genie_sql_service import plant_genie_sql_service


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PlantGenieLiveSample:
    connector_id: str
    connector_name: str
    connector_type: str
    tag: str
    value: Any
    observed_at: datetime
    quality: str | None = None


@dataclass
class OPCUAConnectionResources:
    client: Any
    temp_dir: tempfile.TemporaryDirectory[str] | None = None

    async def close(self) -> None:
        try:
            await self.client.disconnect()
        except Exception:
            pass
        if self.temp_dir is not None:
            self.temp_dir.cleanup()


class PlantGenieConnectorWorker(threading.Thread):
    def __init__(self, runtime: "PlantGeniePlantDataRuntime", connector: PlantGeniePlantDataConnectorRecord) -> None:
        super().__init__(name=f"plant-genie-{connector.connector_type}-{connector.id}", daemon=True)
        self.runtime = runtime
        self.connector = connector
        self.stop_event = threading.Event()

    @property
    def poll_interval_seconds(self) -> float:
        return max(self.connector.poll_interval_ms / 1000.0, 0.5)

    def stop(self) -> None:
        self.stop_event.set()


class OPCUAWorker(PlantGenieConnectorWorker):
    def __init__(self, runtime: "PlantGeniePlantDataRuntime", connector: PlantGeniePlantDataConnectorRecord) -> None:
        super().__init__(runtime, connector)
        self._selected_nodes = _extract_opcua_subscription_nodes(connector.config)
        self._tag_by_node_id = {
            str(node["node_id"]): str(node.get("tag") or node["node_id"])
            for node in self._selected_nodes
        }

    async def _run_subscription_loop(self) -> None:
        resources = await _connect_opcua_client(self.connector.config, self.connector.secrets)
        subscription = None
        try:
            handler = OPCUASubscriptionHandler(self.runtime, self.connector, self._tag_by_node_id)
            subscription = await resources.client.create_subscription(float(max(self.connector.poll_interval_ms, 250)), handler)
            nodes = [resources.client.get_node(str(node["node_id"])) for node in self._selected_nodes]
            if not nodes:
                raise RuntimeError("OPC UA connector has no selected nodes configured.")
            await subscription.subscribe_data_change(nodes, sampling_interval=float(max(self.connector.poll_interval_ms, 250)))
            self.runtime.mark_runtime_healthy(self.connector)
            while not self.stop_event.is_set():
                await resources.client.check_connection()
                if handler.last_error:
                    raise RuntimeError(handler.last_error)
                await asyncio.sleep(1.0)
        finally:
            if subscription is not None:
                try:
                    await subscription.delete()
                except Exception:
                    pass
            await resources.close()

    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        while not self.stop_event.is_set():
            try:
                asyncio.run(self._run_subscription_loop())
            except Exception as exc:
                self.runtime.mark_runtime_error(self.connector, str(exc))
            if self.stop_event.wait(min(self.poll_interval_seconds, 5.0)):
                break
        self.runtime.mark_runtime_stopped(self.connector.id)


class OPCUASubscriptionHandler:
    def __init__(
        self,
        runtime: "PlantGeniePlantDataRuntime",
        connector: PlantGeniePlantDataConnectorRecord,
        tag_by_node_id: Mapping[str, str],
    ) -> None:
        self.runtime = runtime
        self.connector = connector
        self.tag_by_node_id = {str(key): str(value) for key, value in tag_by_node_id.items()}
        self.last_error: str | None = None

    def datachange_notification(self, node, value, data) -> None:  # type: ignore[no-untyped-def]
        node_id = str(node.nodeid.to_string())
        tag = self.tag_by_node_id.get(node_id, node_id)
        quality = None
        try:
            quality = str(data.monitored_item.Value.StatusCode)  # type: ignore[attr-defined]
        except Exception:
            quality = "good"
        self.runtime.record_sample(
            self.connector,
            tag=tag,
            value=value,
            observed_at=_utc_now(),
            quality=quality,
        )

    def status_change_notification(self, status) -> None:  # type: ignore[no-untyped-def]
        self.last_error = str(status)


class MQTTWorker(PlantGenieConnectorWorker):
    def __init__(self, runtime: "PlantGeniePlantDataRuntime", connector: PlantGeniePlantDataConnectorRecord) -> None:
        super().__init__(runtime, connector)
        self._connected = threading.Event()
        self._client: Any | None = None

    def _on_connect(self, client, userdata, flags, rc, properties=None) -> None:  # type: ignore[no-untyped-def]
        _ = userdata
        _ = flags
        _ = properties
        if rc == 0:
            topic = str(self.connector.config["topic"])
            qos = int(self.connector.config.get("qos") or 0)
            client.subscribe(topic, qos=qos)
            self._connected.set()
            self.runtime.mark_runtime_healthy(self.connector)
        else:
            self.runtime.mark_runtime_error(self.connector, f"MQTT connect failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None) -> None:  # type: ignore[no-untyped-def]
        _ = client
        _ = userdata
        _ = properties
        self._connected.clear()
        if self.stop_event.is_set() or rc == 0:
                        return
        self.runtime.mark_runtime_error(self.connector, f"MQTT connection dropped (code {rc}). Reconnecting...")

    def _on_message(self, client, userdata, message) -> None:  # type: ignore[no-untyped-def]
        _ = client
        _ = userdata
        payload_text = message.payload.decode("utf-8", errors="replace").strip()
        observed_at = _utc_now()
        try:
            parsed = json.loads(payload_text)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, dict) and parsed.get("tag") is not None:
            self.runtime.record_sample(
                self.connector,
                tag=str(parsed.get("tag")),
                value=parsed.get("value"),
                observed_at=observed_at,
                quality=str(parsed.get("quality")) if parsed.get("quality") is not None else None,
            )
            return

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("tag") is not None:
                    self.runtime.record_sample(
                        self.connector,
                        tag=str(item.get("tag")),
                        value=item.get("value"),
                        observed_at=observed_at,
                        quality=str(item.get("quality")) if item.get("quality") is not None else None,
                    )
            return

        self.runtime.record_sample(
            self.connector,
            tag=str(message.topic),
            value=payload_text,
            observed_at=observed_at,
            quality=None,
        )

    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        if mqtt is None:
            self.runtime.mark_runtime_error(self.connector, "paho-mqtt is not installed in this environment.")
            self.runtime.mark_runtime_stopped(self.connector.id)
            return

        try:
            client, keep_alive = _build_mqtt_client(self.connector, client_id=self.connector.config.get("client_id") or f"plant-genie-{self.connector.id}")
        except Exception as exc:
            self.runtime.mark_runtime_error(self.connector, str(exc))
            self.runtime.mark_runtime_stopped(self.connector.id)
            return

        self._client = client
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        host, port = _resolve_mqtt_host_port(self.connector.config)

        try:
            client.reconnect_delay_set(min_delay=1, max_delay=30)
            client.connect_async(host, port, keep_alive)
            client.loop_start()
            while not self.stop_event.wait(1.0):
                continue
        except Exception as exc:
            self.runtime.mark_runtime_error(self.connector, str(exc))
        finally:
            try:
                client.disconnect()
            except Exception:
                pass
            try:
                client.loop_stop()
            except Exception:
                pass
            self.runtime.mark_runtime_stopped(self.connector.id)


class SQLWorker(PlantGenieConnectorWorker):
    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        while not self.stop_event.is_set():
            try:
                samples = plant_genie_sql_service.fetch_runtime_samples(self.connector.config, self.connector.secrets)
                for sample in samples:
                    self.runtime.record_sample(
                        self.connector,
                        tag=sample.tag,
                        value=sample.value,
                        observed_at=sample.observed_at,
                        quality=sample.quality,
                    )
                self.runtime.mark_runtime_healthy(self.connector)
            except Exception as exc:
                self.runtime.mark_runtime_error(self.connector, str(exc))
            self.stop_event.wait(self.poll_interval_seconds)
        self.runtime.mark_runtime_stopped(self.connector.id)


class ModbusTCPWorker(PlantGenieConnectorWorker):
    def __init__(self, runtime: "PlantGeniePlantDataRuntime", connector: PlantGeniePlantDataConnectorRecord) -> None:
        super().__init__(runtime, connector)
        self._client: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            self._client = plant_genie_modbus_service.create_client(self.connector.config)
        plant_genie_modbus_service.ensure_connected(self._client)
        return self._client

    def _close_client(self) -> None:
        if self._client is not None:
            plant_genie_modbus_service.close_client(self._client)
            self._client = None

    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        try:
            while not self.stop_event.is_set():
                try:
                    client = self._ensure_client()
                    samples = plant_genie_modbus_service.fetch_runtime_samples(self.connector.config, client=client)
                    for sample in samples:
                        self.runtime.record_sample(
                            self.connector,
                            tag=sample.tag,
                            value=sample.value,
                            observed_at=sample.observed_at,
                            quality=sample.quality,
                        )
                    self.runtime.mark_runtime_healthy(self.connector)
                except Exception as exc:
                    self.runtime.mark_runtime_error(self.connector, str(exc))
                    if bool(self.connector.config.get("auto_reconnect", True)):
                        self._close_client()
                self.stop_event.wait(self.poll_interval_seconds)
        finally:
            self._close_client()
            self.runtime.mark_runtime_stopped(self.connector.id)


class HistorianWorker(PlantGenieConnectorWorker):
    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        while not self.stop_event.is_set():
            try:
                samples = plant_genie_historian_service.fetch_runtime_samples(self.connector.config, self.connector.secrets)
                for sample in samples:
                    self.runtime.record_sample(
                        self.connector,
                        tag=sample.tag,
                        value=sample.value,
                        observed_at=sample.timestamp,
                        quality=sample.quality,
                    )
                self.runtime.mark_runtime_healthy(self.connector)
            except Exception as exc:
                self.runtime.mark_runtime_error(self.connector, str(exc))
            self.stop_event.wait(self.poll_interval_seconds)
        self.runtime.mark_runtime_stopped(self.connector.id)


class PlantGeniePlantDataRuntime:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workers: dict[str, PlantGenieConnectorWorker] = {}
        self._connector_meta: dict[str, PlantGeniePlantDataConnectorRecord] = {}
        self._samples: dict[str, dict[str, PlantGenieLiveSample]] = {}

    def start_enabled_connectors(self) -> None:
        connectors = plant_genie_plant_data_connector_service.list_enabled_connector_records()
        for connector in connectors:
            self.start_connector(connector)

    def start_connector(self, connector: PlantGeniePlantDataConnectorRecord) -> None:
        with self._lock:
            existing = self._workers.get(connector.id)
            if existing is not None and existing.is_alive():
                return
            worker = self._build_worker(connector)
            self._connector_meta[connector.id] = connector
            self._workers[connector.id] = worker
            self._sync_connector_metadata(connector, enabled=True)
            worker.start()

    def stop_connector(self, connector_id: str) -> None:
        with self._lock:
            worker = self._workers.pop(connector_id, None)
        if worker is None:
            with self._lock:
                self._samples.pop(connector_id, None)
                connector = self._connector_meta.pop(connector_id, None)
            if connector is not None:
                self._sync_connector_metadata(connector, enabled=False)
            plant_genie_plant_data_connector_service.update_runtime_state(
                connector_id,
                running=False,
                healthy=False,
                last_error=None,
            )
            return
        worker.stop()
        worker.join(timeout=5.0)
        with self._lock:
            self._samples.pop(connector_id, None)
            connector = self._connector_meta.pop(connector_id, None)
        if connector is not None:
            if connector.connector_type == "sql":
                plant_genie_sql_service.close_pool(connector.config, connector.secrets)
            self._sync_connector_metadata(connector, enabled=False)
        plant_genie_plant_data_connector_service.update_runtime_state(
            connector_id,
            running=False,
            healthy=False,
            last_error=None,
        )

    def stop_all(self) -> None:
        with self._lock:
            connector_ids = list(self._workers.keys())
        for connector_id in connector_ids:
            self.stop_connector(connector_id)

    def record_sample(
        self,
        connector: PlantGeniePlantDataConnectorRecord,
        *,
        tag: str,
        value: Any,
        observed_at: datetime,
        quality: str | None,
    ) -> None:
        sample = PlantGenieLiveSample(
            connector_id=connector.id,
            connector_name=connector.name,
            connector_type=connector.connector_type,
            tag=tag,
            value=value,
            observed_at=observed_at,
            quality=quality,
        )
        with self._lock:
            self._samples.setdefault(connector.id, {})[tag] = sample
            self._connector_meta[connector.id] = connector
        self._push_sample_to_uns(sample)
        self._persist_sample_to_time_series(sample)
        plant_genie_plant_data_connector_service.update_runtime_state(
            connector.id,
            running=True,
            healthy=True,
            last_update=observed_at,
            last_error=None,
        )

    def mark_runtime_started(self, connector: PlantGeniePlantDataConnectorRecord) -> None:
        with self._lock:
            self._connector_meta[connector.id] = connector
        self._sync_connector_metadata(connector, enabled=True)
        plant_genie_plant_data_connector_service.update_runtime_state(
            connector.id,
            running=True,
            healthy=False,
            last_error=None,
        )

    def mark_runtime_healthy(self, connector: PlantGeniePlantDataConnectorRecord) -> None:
        plant_genie_plant_data_connector_service.update_runtime_state(
            connector.id,
            running=True,
            healthy=True,
            last_error=None,
        )

    def mark_runtime_error(self, connector: PlantGeniePlantDataConnectorRecord, error: str) -> None:
        logger.warning("Plant Genie connector %s failed: %s", connector.id, error)
        plant_genie_plant_data_connector_service.update_runtime_state(
            connector.id,
            running=True,
            healthy=False,
            last_error=error[:4000],
        )

    def mark_runtime_stopped(self, connector_id: str) -> None:
        plant_genie_plant_data_connector_service.update_runtime_state(
            connector_id,
            running=False,
            healthy=False,
        )

    def build_query_context(
        self,
        user_id: str,
        selected_tag: str | None = None,
        binding_config: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            user_samples: list[PlantGenieLiveSample] = []
            for connector_id, connector in self._connector_meta.items():
                if connector.user_id != user_id:
                    continue
                user_samples.extend(self._samples.get(connector_id, {}).values())

        binding = _normalize_ai_binding_config(binding_config)
        if binding.get("data_source_connector_id"):
            user_samples = [sample for sample in user_samples if sample.connector_id == binding["data_source_connector_id"]]

        allowed_tags = set(binding.get("selected_tags") or []) if binding.get("tag_scope") == "selected" else None
        if allowed_tags is not None:
            user_samples = [sample for sample in user_samples if sample.tag in allowed_tags]

        user_samples.sort(key=lambda item: item.observed_at, reverse=True)
        connector_names = sorted({sample.connector_name for sample in user_samples})
        context_tags = _resolve_context_tags(user_samples, selected_tag=selected_tag, binding=binding)
        live_context: dict[str, Any] = {
            "source": "live_plant_connectors",
            "sample_count": len(user_samples),
            "connectors": connector_names,
            "latest_samples": [
                {
                    "tag": sample.tag,
                    "value": sample.value,
                    "observed_at": sample.observed_at.isoformat(),
                    "quality": sample.quality,
                    "connector_type": sample.connector_type,
                }
                for sample in user_samples[:20]
            ],
            "ai_binding": {
                "configured": bool(binding.get("configured")),
                "data_source_connector_id": binding.get("data_source_connector_id"),
                "tag_scope": binding.get("tag_scope") or "all",
                "selected_tags": list(binding.get("selected_tags") or []),
                "context_mode": binding.get("context_mode") or "live_only",
                "sampling_mode": binding.get("sampling_mode") or "stream",
                "sampling_interval_ms": binding.get("sampling_interval_ms"),
                "ai_access_mode": binding.get("ai_access_mode") or "read_only",
                "include_system_structure": bool(binding.get("include_system_structure")),
                "ai_api_input": binding.get("ai_api_input"),
            },
        }
        normalized_tag = str(selected_tag or "").strip()
        if normalized_tag:
            matching = [sample for sample in user_samples if sample.tag == normalized_tag]
            if matching:
                sample = matching[0]
                live_context["selected_tag"] = {
                    "tag": sample.tag,
                    "value": sample.value,
                    "observed_at": sample.observed_at.isoformat(),
                    "quality": sample.quality,
                    "connector_name": sample.connector_name,
                    "connector_type": sample.connector_type,
                }
        context_mode = str(binding.get("context_mode") or "live_only")
        if context_mode in {"historical", "hybrid"} and context_tags:
            history_points = 24 if str(binding.get("sampling_mode") or "stream") == "interval" else 12
            live_context["historical_samples"] = influx_client.get_signal_history(context_tags, points=history_points)
        if bool(binding.get("include_system_structure")):
            live_context["system_structure"] = _build_system_structure_context(context_tags)
        return live_context

    def test_connector(self, connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        if connector.connector_type == "opcua":
            return self._test_opcua(connector)
        if connector.connector_type == "mqtt":
            return self._test_mqtt(connector)
        if connector.connector_type == "modbus_tcp":
            return self._test_modbus(connector)
        if connector.connector_type == "historian":
            return self._test_historian(connector)
        return self._test_sql(connector)

    def _build_worker(self, connector: PlantGeniePlantDataConnectorRecord) -> PlantGenieConnectorWorker:
        if connector.connector_type == "opcua":
            return OPCUAWorker(self, connector)
        if connector.connector_type == "mqtt":
            return MQTTWorker(self, connector)
        if connector.connector_type == "modbus_tcp":
            return ModbusTCPWorker(self, connector)
        if connector.connector_type == "historian":
            return HistorianWorker(self, connector)
        return SQLWorker(self, connector)

    def browse_opcua(self, config: dict[str, Any], secrets: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
        async def run_browse() -> dict[str, Any]:
            resources = await _connect_opcua_client(config, secrets)
            try:
                if node_id:
                    browse_node = resources.client.get_node(str(node_id))
                else:
                    browse_node = resources.client.get_objects_node()
                browse_name = await browse_node.read_browse_name()
                display_name = await browse_node.read_display_name()
                children = await browse_node.get_children()
                nodes: list[dict[str, Any]] = []
                for child in children[:200]:
                    child_browse_name = await child.read_browse_name()
                    child_display_name = await child.read_display_name()
                    child_node_class = await child.read_node_class()
                    child_children = await child.get_children()
                    node_class_name = _format_opcua_node_class(child_node_class)
                    nodes.append(
                        {
                            "node_id": str(child.nodeid.to_string()),
                            "browse_name": str(getattr(child_browse_name, "Name", "") or str(child.nodeid.to_string())),
                            "display_name": str(getattr(child_display_name, "Text", "") or getattr(child_browse_name, "Name", "") or str(child.nodeid.to_string())),
                            "node_class": node_class_name,
                            "has_children": bool(child_children),
                            "selectable": node_class_name == "Variable",
                        }
                    )
                return {
                    "node_id": str(browse_node.nodeid.to_string()),
                    "browse_name": str(getattr(browse_name, "Name", "") or str(browse_node.nodeid.to_string())),
                    "display_name": str(getattr(display_name, "Text", "") or getattr(browse_name, "Name", "") or str(browse_node.nodeid.to_string())),
                    "nodes": nodes,
                }
            finally:
                await resources.close()

        return asyncio.run(run_browse())

    def sql_schema(self, config: dict[str, Any], secrets: dict[str, Any], *, table_name: str | None = None, table_schema: str | None = None) -> dict[str, Any]:
        tables = plant_genie_sql_service.list_tables(config, secrets)
        columns: list[dict[str, Any]] = []
        resolved_table_name = str(table_name or config.get("table_name") or "").strip() or None
        resolved_table_schema = str(table_schema or config.get("table_schema") or "").strip() or None
        if resolved_table_name:
            columns = plant_genie_sql_service.list_columns(
                config,
                secrets,
                table_name=resolved_table_name,
                table_schema=resolved_table_schema,
            )
        return {
            "tables": tables,
            "columns": columns,
        }

    def preview_sql(self, config: dict[str, Any], secrets: dict[str, Any], *, limit: int = 25) -> dict[str, Any]:
        return plant_genie_sql_service.preview_data(config, secrets, limit=limit)

    def preview_modbus(self, config: dict[str, Any], secrets: dict[str, Any]) -> dict[str, Any]:
        _ = secrets
        return plant_genie_modbus_service.preview_data(config)

    def browse_historian(self, config: dict[str, Any], secrets: dict[str, Any], *, query: str | None = None, limit: int = 50) -> dict[str, Any]:
        return {
            "items": plant_genie_historian_service.browse_pi_assets(config, secrets, query=query, limit=limit),
        }

    def preview_historian(self, config: dict[str, Any], secrets: dict[str, Any]) -> dict[str, Any]:
        return plant_genie_historian_service.preview_data(config, secrets)

    def _push_sample_to_uns(self, sample: PlantGenieLiveSample) -> None:
        patch = {
            "current_value": _stringify_runtime_value(sample.value),
        }
        if sample.quality:
            patch["state"] = sample.quality
        try:
            uns_core.update_runtime({sample.tag: patch})
        except Exception:
            logger.debug("Failed to mirror connector sample into UNS for tag=%s", sample.tag, exc_info=True)

    def _persist_sample_to_time_series(self, sample: PlantGenieLiveSample) -> None:
        try:
            influx_client.write_signal_samples(
                [
                    {
                        "tag": sample.tag,
                        "timestamp": sample.observed_at,
                        "value": sample.value,
                        "quality": sample.quality,
                        "connector_type": sample.connector_type,
                    }
                ]
            )
        except Exception:
            logger.debug("Failed to persist connector sample to time-series storage for tag=%s", sample.tag, exc_info=True)

    def _sync_connector_metadata(self, connector: PlantGeniePlantDataConnectorRecord, *, enabled: bool) -> None:
        if connector.connector_type not in {"opcua", "mqtt", "modbus_tcp", "historian"}:
            return
        metadata = {
            "connector_id": connector.id,
            "connector_name": connector.name,
            "enabled": enabled,
            "selected_tags": _extract_connector_selected_tags(connector),
        }
        if connector.connector_type == "opcua":
            metadata["endpoint"] = str(connector.config.get("server_url") or connector.config.get("endpoint") or "")
        if connector.connector_type == "mqtt":
            metadata["topic"] = str(connector.config.get("topic") or "")
        if connector.connector_type == "modbus_tcp":
            metadata["endpoint"] = f"{str(connector.config.get('host') or '')}:{int(connector.config.get('port') or 502)}"
        if connector.connector_type == "historian":
            metadata["endpoint"] = str(connector.config.get("pi_server_url") or connector.config.get("endpoint_url") or connector.config.get("host") or "")
        try:
            uns_core.set_connector(connector.connector_type, metadata)
        except Exception:
            logger.debug("Failed to update UNS connector metadata for connector=%s", connector.id, exc_info=True)

    @staticmethod
    def _test_opcua(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        if AsyncUAClient is None:
            return False, "OPC UA connector is unavailable on the server (missing asyncua dependency)."

        async def run_test() -> tuple[bool, str]:
            resources = await _connect_opcua_client(connector.config, connector.secrets)
            try:
                client = resources.client
                node_ids = list(connector.config.get("node_ids") or [])
                if node_ids:
                    node = client.get_node(str(node_ids[0]))
                    await node.read_value()
                return True, "OPC UA server reachable."
            finally:
                await resources.close()

        try:
            return asyncio.run(run_test())
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _test_mqtt(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        if mqtt is None:
            return False, "MQTT connector is unavailable on the server (missing paho-mqtt dependency)."

        host, port = _resolve_mqtt_host_port(connector.config)

        try:
            client, keep_alive = _build_mqtt_client(connector, client_id=connector.config.get("client_id") or f"plant-genie-test-{connector.id}")
            client.connect(host, port, keep_alive)
            client.disconnect()
            return True, "MQTT broker reachable."
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _test_sql(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        try:
            return plant_genie_sql_service.test_connection(connector.config, connector.secrets)
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _test_modbus(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        try:
            return plant_genie_modbus_service.test_connection(connector.config)
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _test_historian(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        try:
            return plant_genie_historian_service.test_connection(connector.config, connector.secrets)
        except Exception as exc:
            return False, str(exc)


def _normalize_ai_binding_config(binding_config: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(binding_config, Mapping):
        return {"configured": False}
    selected_tags = [str(tag).strip() for tag in binding_config.get("selected_tags", []) if str(tag).strip()]
    return {
        "configured": True,
        "data_source_connector_id": str(binding_config.get("data_source_connector_id") or "").strip() or None,
        "tag_scope": str(binding_config.get("tag_scope") or "all").strip() or "all",
        "selected_tags": selected_tags,
        "context_mode": str(binding_config.get("context_mode") or "live_only").strip() or "live_only",
        "sampling_mode": str(binding_config.get("sampling_mode") or "stream").strip() or "stream",
        "sampling_interval_ms": binding_config.get("sampling_interval_ms"),
        "ai_access_mode": str(binding_config.get("ai_access_mode") or "read_only").strip() or "read_only",
        "include_system_structure": bool(binding_config.get("include_system_structure")),
        "ai_api_input": str(binding_config.get("ai_api_input") or "").strip() or None,
    }


def _resolve_context_tags(
    samples: list[PlantGenieLiveSample],
    *,
    selected_tag: str | None,
    binding: Mapping[str, Any],
) -> list[str]:
    if binding.get("tag_scope") == "selected":
        return [str(tag).strip() for tag in binding.get("selected_tags") or [] if str(tag).strip()]
    normalized_selected_tag = str(selected_tag or "").strip()
    if normalized_selected_tag:
        return [normalized_selected_tag]
    ordered: list[str] = []
    seen: set[str] = set()
    for sample in samples:
        if sample.tag in seen:
            continue
        seen.add(sample.tag)
        ordered.append(sample.tag)
        if len(ordered) >= 20:
            break
    return ordered


def _build_system_structure_context(tags: list[str]) -> dict[str, Any]:
    normalized_tags = {str(tag).strip() for tag in tags if str(tag).strip()}
    loops = control_loop_store.list_loops()
    matching_loops = []
    for loop in loops:
        loop_tags = {
            str(loop.loop_tag or "").strip(),
            str(loop.sensor_tag or "").strip(),
            str(loop.actuator_tag or "").strip(),
            str(loop.controller_tag or "").strip(),
            str(loop.setpoint_tag or "").strip(),
            str(loop.output_tag or "").strip(),
        }
        if normalized_tags and not (loop_tags & normalized_tags):
            continue
        matching_loops.append(
            {
                "loop_tag": loop.loop_tag,
                "sensor_tag": loop.sensor_tag,
                "actuator_tag": loop.actuator_tag,
                "controller_tag": loop.controller_tag,
                "process_unit": loop.process_unit,
                "control_strategy": loop.control_strategy,
                "status": loop.status,
            }
        )
        if len(matching_loops) >= 12:
            break
    equipment = sorted({str(loop.get("process_unit") or "").strip() for loop in matching_loops if str(loop.get("process_unit") or "").strip()})
    return {
        "control_loops": matching_loops,
        "equipment": equipment,
    }


def _resolve_mqtt_host_port(config: Mapping[str, Any]) -> tuple[str, int]:
    broker_url = str(config.get("broker_url") or "").strip()
    if broker_url:
        normalized = broker_url if "://" in broker_url else f"mqtt://{broker_url}"
        parsed = urlparse(normalized)
        host = parsed.hostname or ""
        port = int(parsed.port or config.get("port") or 1883)
        return host, port
    return str(config.get("host") or "").strip(), int(config.get("port") or 1883)


def _build_mqtt_client(connector: PlantGeniePlantDataConnectorRecord, *, client_id: str | None = None):
    if mqtt is None:
        raise RuntimeError("MQTT connector is unavailable on the server (missing paho-mqtt dependency).")

    client = mqtt.Client(client_id=str(client_id or connector.config.get("client_id") or f"plant-genie-{connector.id}"))
    client.enable_logger(logger)

    username = connector.config.get("username")
    password = connector.secrets.get("password")
    if username:
        client.username_pw_set(str(username), str(password or ""))

    broker_url = str(connector.config.get("broker_url") or "").strip().lower()
    tls_enabled = bool(connector.config.get("tls_enabled")) or broker_url.startswith("mqtts://")
    if tls_enabled:
        ssl_context = ssl.create_default_context()
        ca_certificate = str(connector.secrets.get("ca_certificate_pem") or "").strip()
        if ca_certificate:
            ssl_context.load_verify_locations(cadata=ca_certificate)
        client.tls_set_context(ssl_context)

    keep_alive = int(connector.config.get("keep_alive") or 30)
    return client, keep_alive


def _stringify_runtime_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    try:
        return json.dumps(value)
    except Exception:
        return str(value)


def _format_opcua_node_class(value: Any) -> str:
    name = getattr(value, "name", None)
    if name:
        return str(name)
    return str(value)


def _extract_opcua_subscription_nodes(config: Mapping[str, Any]) -> list[dict[str, str]]:
    subscription_config = config.get("subscription_config")
    selected_nodes: list[dict[str, str]] = []
    if isinstance(subscription_config, dict):
        raw_nodes = subscription_config.get("nodes") or subscription_config.get("selected_nodes") or subscription_config.get("subscriptions")
        if isinstance(raw_nodes, list):
            for item in raw_nodes:
                if isinstance(item, dict):
                    node_id = str(item.get("node_id") or item.get("nodeId") or item.get("id") or "").strip()
                    if not node_id:
                        continue
                    selected_nodes.append(
                        {
                            "node_id": node_id,
                            "browse_name": str(item.get("browse_name") or item.get("browseName") or node_id).strip() or node_id,
                            "display_name": str(item.get("display_name") or item.get("displayName") or item.get("browse_name") or item.get("browseName") or node_id).strip() or node_id,
                            "node_class": str(item.get("node_class") or item.get("nodeClass") or "Variable").strip() or "Variable",
                            "tag": str(item.get("tag") or item.get("display_name") or item.get("displayName") or item.get("browse_name") or item.get("browseName") or node_id).strip() or node_id,
                        }
                    )
    if selected_nodes:
        return selected_nodes

    for node_id in config.get("node_ids") or []:
        normalized = str(node_id).strip()
        if normalized:
            selected_nodes.append(
                {
                    "node_id": normalized,
                    "browse_name": normalized,
                    "display_name": normalized,
                    "node_class": "Variable",
                    "tag": normalized,
                }
            )
    return selected_nodes


def _extract_connector_selected_tags(connector: PlantGeniePlantDataConnectorRecord) -> list[str]:
    if connector.connector_type == "opcua":
        return [str(node.get("tag") or node.get("node_id") or "") for node in _extract_opcua_subscription_nodes(connector.config) if str(node.get("tag") or node.get("node_id") or "").strip()]
    if connector.connector_type == "modbus_tcp":
        return [
            str(mapping.get("internal_tag") or "").strip()
            for mapping in connector.config.get("tag_mappings") or []
            if isinstance(mapping, Mapping) and str(mapping.get("internal_tag") or "").strip()
        ]
    if connector.connector_type == "historian":
        return [
            str(mapping.get("internal_tag") or "").strip()
            for mapping in connector.config.get("tag_mappings") or []
            if isinstance(mapping, Mapping) and str(mapping.get("internal_tag") or "").strip()
        ]
    return [str(tag).strip() for tag in connector.config.get("node_ids") or [] if str(tag).strip()]


def _opcua_security_policy_token(policy: str | None) -> str:
    normalized = str(policy or "").strip().lower()
    mapping = {
        "basic256sha256": "Basic256Sha256",
        "aes128sha256rsaoaep": "Aes128Sha256RsaOaep",
        "aes256sha256rsapss": "Aes256Sha256RsaPss",
    }
    if normalized not in mapping:
        raise RuntimeError("Unsupported OPC UA security policy configuration.")
    return mapping[normalized]


def _opcua_security_mode_token(mode: str | None) -> str:
    normalized = str(mode or "").strip().lower()
    mapping = {
        "sign": "Sign",
        "sign_and_encrypt": "SignAndEncrypt",
    }
    if normalized not in mapping:
        raise RuntimeError("Unsupported OPC UA security mode configuration.")
    return mapping[normalized]


def _write_text_file(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


async def _connect_opcua_client(config: Mapping[str, Any], secrets: Mapping[str, Any]) -> OPCUAConnectionResources:
    if AsyncUAClient is None:
        raise RuntimeError("asyncua is not installed in this environment.")

    endpoint = str(config.get("endpoint") or config.get("server_url") or "").strip()
    if not endpoint:
        raise RuntimeError("OPC UA endpoint is missing.")

    temp_dir = tempfile.TemporaryDirectory(prefix="opcua-connector-")
    temp_path = Path(temp_dir.name)
    trust_list_pems = [str(item).strip() for item in secrets.get("trust_list_pems") or [] if str(item).strip()]
    trust_cert_paths = [
        _write_text_file(temp_path, f"trusted-server-{index + 1}.pem", certificate)
        for index, certificate in enumerate(trust_list_pems)
    ]

    client_certificate_path: Path | None = None
    client_private_key_path: Path | None = None
    if str(config.get("security_mode") or "").strip():
        certificate_pem = str(secrets.get("client_certificate_pem") or "").strip()
        private_key_pem = str(secrets.get("client_private_key_pem") or "").strip()
        if not certificate_pem or not private_key_pem:
            temp_dir.cleanup()
            raise RuntimeError("Secure OPC UA sessions require a stored client certificate and private key.")
        client_certificate_path = _write_text_file(temp_path, str(config.get("client_certificate_name") or "client-cert.pem"), certificate_pem)
        client_private_key_path = _write_text_file(temp_path, str(config.get("client_private_key_name") or "client-key.pem"), private_key_pem)

    candidates: list[Path | None] = trust_cert_paths or [None]
    last_error: Exception | None = None
    for server_certificate_path in candidates:
        client = AsyncUAClient(url=endpoint)
        try:
            client.session_timeout = float(int(config.get("session_timeout_ms") or 60000))
            auth_mode = str(config.get("authentication_mode") or "anonymous")
            username = str(config.get("username") or "").strip()
            password = str(secrets.get("password") or "")
            if auth_mode == "username_password" and username:
                client.set_user(username)
                client.set_password(password)

            security_mode = str(config.get("security_mode") or "").strip()
            if security_mode:
                if client_certificate_path is None or client_private_key_path is None:
                    raise RuntimeError("Secure OPC UA sessions require client certificate material.")
                key_path = str(client_private_key_path)
                private_key_password = str(secrets.get("client_private_key_password") or "").strip()
                if private_key_password:
                    key_path = f"{key_path}::{private_key_password}"
                security_string = ",".join(
                    part
                    for part in [
                        _opcua_security_policy_token(str(config.get("security_policy") or "")),
                        _opcua_security_mode_token(security_mode),
                        str(client_certificate_path),
                        key_path,
                        str(server_certificate_path) if server_certificate_path is not None else "",
                    ]
                    if part
                )
                await client.set_security_string(security_string)

            await client.connect()
            return OPCUAConnectionResources(client=client, temp_dir=temp_dir)
        except Exception as exc:
            last_error = exc
            try:
                await client.disconnect()
            except Exception:
                pass

    temp_dir.cleanup()
    if last_error is None:
        raise RuntimeError("OPC UA connection failed.")
    raise RuntimeError(str(last_error))


plant_genie_plant_data_runtime = PlantGeniePlantDataRuntime()