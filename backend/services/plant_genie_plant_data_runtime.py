from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from services.plant_genie_plant_data_service import (
    PlantGeniePlantDataConnectorRecord,
    plant_genie_plant_data_connector_service,
)

try:
    from asyncua import Client as AsyncUAClient  # type: ignore
except Exception:  # pragma: no cover
    AsyncUAClient = None

try:
    import paho.mqtt.client as mqtt  # type: ignore
except Exception:  # pragma: no cover
    mqtt = None

try:
    import psycopg2  # type: ignore
except Exception:  # pragma: no cover
    psycopg2 = None


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
    async def _poll_once(self) -> None:
        if AsyncUAClient is None:
            raise RuntimeError("asyncua is not installed in this environment.")

        client = AsyncUAClient(url=str(self.connector.config["endpoint"]))
        try:
            await client.connect()
            for node_id in self.connector.config.get("node_ids", []):
                node = client.get_node(str(node_id))
                value = await node.read_value()
                self.runtime.record_sample(
                    self.connector,
                    tag=str(node_id),
                    value=value,
                    observed_at=_utc_now(),
                    quality="good",
                )
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        while not self.stop_event.is_set():
            try:
                asyncio.run(self._poll_once())
                self.runtime.mark_runtime_healthy(self.connector)
            except Exception as exc:
                self.runtime.mark_runtime_error(self.connector, str(exc))
            self.stop_event.wait(self.poll_interval_seconds)
        self.runtime.mark_runtime_stopped(self.connector.id)


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

        client = mqtt.Client(client_id=self.connector.config.get("client_id") or f"plant-genie-{self.connector.id}")
        self._client = client
        secrets = self.connector.secrets
        username = self.connector.config.get("username")
        password = secrets.get("password")
        if username:
            client.username_pw_set(str(username), str(password or ""))
        client.on_connect = self._on_connect
        client.on_message = self._on_message

        host, port = _resolve_mqtt_host_port(self.connector.config)

        try:
            client.connect(host, port, 30)
            client.loop_start()
            while not self.stop_event.wait(1.0):
                if not self._connected.is_set():
                    continue
            client.loop_stop()
            client.disconnect()
        except Exception as exc:
            self.runtime.mark_runtime_error(self.connector, str(exc))
        finally:
            self.runtime.mark_runtime_stopped(self.connector.id)


class SQLWorker(PlantGenieConnectorWorker):
    def _connect(self):
        connection_string = _build_sql_connection_string(self.connector.config, self.connector.secrets)

        if connection_string.startswith("sqlite:///"):
            path = connection_string.removeprefix("sqlite:///")
            return sqlite3.connect(path)

        if psycopg2 is None:
            raise RuntimeError("psycopg2 is not installed in this environment.")
        return psycopg2.connect(connection_string)

    def run(self) -> None:
        self.runtime.mark_runtime_started(self.connector)
        while not self.stop_event.is_set():
            conn = None
            try:
                conn = self._connect()
                cursor = conn.cursor()
                cursor.execute(str(self.connector.config["query"]))
                columns = [item[0] for item in cursor.description or []]
                rows = cursor.fetchall()
                tag_column = str(self.connector.config["tag_column"])
                value_column = str(self.connector.config["value_column"])
                timestamp_column = self.connector.config.get("timestamp_column")

                for row in rows:
                    row_map = dict(zip(columns, row))
                    tag = str(row_map.get(tag_column) or "").strip()
                    if not tag:
                        continue
                    observed_raw = row_map.get(timestamp_column) if timestamp_column else None
                    observed_at = observed_raw if isinstance(observed_raw, datetime) else _utc_now()
                    self.runtime.record_sample(
                        self.connector,
                        tag=tag,
                        value=row_map.get(value_column),
                        observed_at=observed_at,
                        quality="good",
                    )
                self.runtime.mark_runtime_healthy(self.connector)
            except Exception as exc:
                self.runtime.mark_runtime_error(self.connector, str(exc))
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass
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
            worker.start()

    def stop_connector(self, connector_id: str) -> None:
        with self._lock:
            worker = self._workers.pop(connector_id, None)
        if worker is None:
            with self._lock:
                self._samples.pop(connector_id, None)
                self._connector_meta.pop(connector_id, None)
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
            self._connector_meta.pop(connector_id, None)
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
            last_error=None,
        )

    def build_query_context(self, user_id: str, selected_tag: str | None = None) -> dict[str, Any]:
        with self._lock:
            user_samples: list[PlantGenieLiveSample] = []
            for connector_id, connector in self._connector_meta.items():
                if connector.user_id != user_id:
                    continue
                user_samples.extend(self._samples.get(connector_id, {}).values())

        user_samples.sort(key=lambda item: item.observed_at, reverse=True)
        live_context: dict[str, Any] = {
            "source": "live_plant_connectors",
            "sample_count": len(user_samples),
            "connectors": sorted({sample.connector_name for sample in user_samples}),
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
        return live_context

    def test_connector(self, connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        if connector.connector_type == "opcua":
            return self._test_opcua(connector)
        if connector.connector_type == "mqtt":
            return self._test_mqtt(connector)
        return self._test_sql(connector)

    def _build_worker(self, connector: PlantGeniePlantDataConnectorRecord) -> PlantGenieConnectorWorker:
        if connector.connector_type == "opcua":
            return OPCUAWorker(self, connector)
        if connector.connector_type == "mqtt":
            return MQTTWorker(self, connector)
        return SQLWorker(self, connector)

    @staticmethod
    def _test_opcua(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        if AsyncUAClient is None:
            return False, "OPC UA connector is unavailable on the server (missing asyncua dependency)."

        async def run_test() -> tuple[bool, str]:
            client = AsyncUAClient(url=str(connector.config.get("endpoint") or connector.config.get("server_url") or ""))
            try:
                await client.connect()
                node_ids = list(connector.config.get("node_ids") or [])
                if node_ids:
                    node = client.get_node(str(node_ids[0]))
                    await node.read_value()
                return True, "OPC UA server reachable."
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        try:
            return asyncio.run(run_test())
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _test_mqtt(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        if mqtt is None:
            return False, "MQTT connector is unavailable on the server (missing paho-mqtt dependency)."

        host, port = _resolve_mqtt_host_port(connector.config)
        client = mqtt.Client(client_id=connector.config.get("client_id") or f"plant-genie-test-{connector.id}")
        username = connector.config.get("username")
        password = connector.secrets.get("password")
        if username:
            client.username_pw_set(str(username), str(password or ""))

        try:
            client.connect(host, port, 15)
            client.disconnect()
            return True, "MQTT broker reachable."
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _test_sql(connector: PlantGeniePlantDataConnectorRecord) -> tuple[bool, str]:
        connection_string = _build_sql_connection_string(connector.config, connector.secrets)
        conn = None
        try:
            if connection_string.startswith("sqlite:///"):
                path = connection_string.removeprefix("sqlite:///")
                conn = sqlite3.connect(path)
            else:
                if psycopg2 is None:
                    return False, "SQL connector is unavailable on the server (missing psycopg2 dependency)."
                conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute(str(connector.config.get("query") or ""))
            cursor.fetchone()
            return True, "SQL / Historian connection succeeded."
        except Exception as exc:
            return False, str(exc)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


def _resolve_mqtt_host_port(config: Mapping[str, Any]) -> tuple[str, int]:
    broker_url = str(config.get("broker_url") or "").strip()
    if broker_url:
        normalized = broker_url if "://" in broker_url else f"mqtt://{broker_url}"
        parsed = urlparse(normalized)
        host = parsed.hostname or ""
        port = int(parsed.port or config.get("port") or 1883)
        return host, port
    return str(config.get("host") or "").strip(), int(config.get("port") or 1883)


def _build_sql_connection_string(config: Mapping[str, Any], secrets: Mapping[str, Any]) -> str:
    connection_string = str(secrets.get("connection_string") or "").strip()
    if connection_string:
        return connection_string

    host = str(config.get("host") or "").strip()
    port = int(config.get("port") or 5432)
    database = str(config.get("database") or "").strip()
    username = str(config.get("username") or "").strip()
    password = str(secrets.get("password") or "").strip()
    if not host or not database or not username or not password:
        raise RuntimeError("SQL connector is missing host, database, username, or password configuration")
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


plant_genie_plant_data_runtime = PlantGeniePlantDataRuntime()