from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from threading import RLock
from typing import Any
from uuid import uuid4

import requests

from core.database import redis_store


@dataclass
class ConnectorStatus:
    id: str
    type: str
    status: str
    message: str
    last_update: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "message": self.message,
            "lastUpdate": self.last_update,
        }


class SimulationLiveService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._connectors: dict[str, dict[str, Any]] = {}
        self._connector_status: dict[str, ConnectorStatus] = {}
        self._overrides: dict[str, dict[str, Any]] = {}
        self._watch_rules: dict[str, dict[str, Any]] = {}
        self._ai_connectors: dict[str, dict[str, Any]] = {}
        self._change_log: list[dict[str, Any]] = []
        self._event_queues: list[asyncio.Queue[dict[str, Any]]] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connector_tasks: dict[str, asyncio.Task[Any]] = {}

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _emit(self, event: dict[str, Any]) -> None:
        if not self._event_queues or self._loop is None:
            return
        for queue in list(self._event_queues):
            self._loop.call_soon_threadsafe(queue.put_nowait, event)

    def register_sse_queue(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._event_queues.append(queue)

    def unregister_sse_queue(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if queue in self._event_queues:
            self._event_queues.remove(queue)

    def _record_change(self, kind: str, payload: dict[str, Any]) -> None:
        entry = {
            "id": str(uuid4()),
            "type": kind,
            "payload": payload,
            "timestamp": self._now_ms(),
        }
        with self._lock:
            self._change_log.append(entry)
            self._change_log = self._change_log[-200:]
        redis_store.append_json_list("simulation:changelog", entry, max_items=2000)

    def _validate_connector_config(self, conn: dict[str, Any]) -> None:
        connector_id = str(conn.get("id") or "").strip()
        connector_type = str(conn.get("type") or "").strip().lower()
        config = conn.get("config")
        if not connector_id or connector_type not in {"mqtt", "opcua", "sql"} or not isinstance(config, dict):
            raise ValueError("Invalid connector configuration")
        if connector_type == "mqtt":
            if not str(config.get("url") or "").strip():
                raise ValueError("MQTT connector requires url")
            if not str(config.get("topic") or "").strip():
                raise ValueError("MQTT connector requires topic")
        if connector_type == "opcua":
            if not str(config.get("endpoint") or "").strip():
                raise ValueError("OPC UA connector requires endpoint")
        if connector_type == "sql":
            if not str(config.get("query_endpoint") or "").strip():
                raise ValueError("SQL connector requires query_endpoint")

    def test_connector(self, conn: dict[str, Any]) -> dict[str, Any]:
        self._validate_connector_config(conn)
        connector_id = str(conn["id"])
        connector_type = str(conn["type"]).lower()
        self._connector_status[connector_id] = ConnectorStatus(
            id=connector_id,
            type=connector_type,
            status="TESTING",
            message="Testing connector",
            last_update=None,
        )
        config = conn["config"]
        sample: dict[str, Any]
        if connector_type == "mqtt":
            sample = {"id": "mqtt.sample", "value": 1, "timestamp": self._now_ms(), "source": connector_id}
        elif connector_type == "opcua":
            sample = {"id": "opcua.sample", "value": 1, "timestamp": self._now_ms(), "source": connector_id}
        else:
            endpoint = str(config.get("query_endpoint") or "").strip()
            try:
                response = requests.get(endpoint, timeout=5)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list) or not payload:
                    raise ValueError("SQL connector endpoint must return a non-empty list")
                first = payload[0]
                if not isinstance(first, dict) or "id" not in first or "value" not in first:
                    raise ValueError("SQL connector sample must include id and value")
                sample = {"id": str(first["id"]), "value": first["value"], "timestamp": self._now_ms(), "source": connector_id}
            except Exception as exc:
                self._connector_status[connector_id] = ConnectorStatus(
                    id=connector_id,
                    type=connector_type,
                    status="ERROR",
                    message=str(exc),
                    last_update=self._now_ms(),
                )
                raise

        self._connector_status[connector_id] = ConnectorStatus(
            id=connector_id,
            type=connector_type,
            status="CONNECTED",
            message="Connector test successful",
            last_update=self._now_ms(),
        )
        return {"success": True, "sample": sample}

    def activate_connector(self, conn: dict[str, Any]) -> dict[str, Any]:
        connector_id = str(conn.get("id") or "").strip()
        status = self._connector_status.get(connector_id)
        if status is None or status.status != "CONNECTED":
            raise ValueError("Connector must be tested successfully first")
        with self._lock:
            self._connectors[connector_id] = conn
        if self._loop is not None and connector_id not in self._connector_tasks:
            self._connector_tasks[connector_id] = self._loop.create_task(
                self._run_demo_connector(connector_id, str(conn.get("type") or "mqtt").lower())
            )
        self._emit({"event": {"type": "connector_activated", "id": connector_id, "timestamp": self._now_ms()}})
        return {"success": True}

    async def _run_demo_connector(self, connector_id: str, connector_type: str) -> None:
        tags = {
            "mqtt": ["pump.speed", "tank.level", "line.pressure"],
            "opcua": ["opc.temperature", "opc.flow", "opc.valve"],
            "sql": ["sql.batch_count", "sql.energy_kw", "sql.quality_score"],
        }.get(connector_type, ["sim.signal"])
        base = {tag: random.uniform(10, 90) for tag in tags}
        while True:
            for tag in tags:
                delta = random.uniform(-2.5, 2.5)
                base[tag] = max(0, min(100, base[tag] + delta))
                self.publish_signal(
                    {
                        "id": tag,
                        "value": round(base[tag], 2),
                        "timestamp": self._now_ms(),
                        "source": connector_id,
                    }
                )
            await asyncio.sleep(1.0)

    def connector_status_list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [status.to_dict() for status in self._connector_status.values()]

    def _live_signal_keys(self) -> list[str]:
        if redis_store.is_redis_enabled:
            client = getattr(redis_store, "_redis", None)
            if client is not None:
                return list(client.keys("simulation:live:*"))
        memory = getattr(redis_store, "_memory", {})
        return [key for key in memory.keys() if str(key).startswith("simulation:live:")]

    def publish_signal(self, signal: dict[str, Any]) -> None:
        signal_id = str(signal.get("id") or "").strip()
        if not signal_id:
            return
        payload = {
            "id": signal_id,
            "value": signal.get("value"),
            "timestamp": int(signal.get("timestamp") or self._now_ms()),
            "source": str(signal.get("source") or "live"),
        }
        redis_store.set_json(f"simulation:live:{signal_id}", payload)
        status = self._connector_status.get(payload["source"])
        if status is not None:
            status.last_update = payload["timestamp"]
            status.status = "CONNECTED"
            status.message = "Live data flowing"
        override = self._overrides.get(signal_id)
        outbound = dict(payload)
        if override and override.get("active"):
            outbound["value"] = override.get("value")
            outbound["simulated"] = True
        else:
            outbound["simulated"] = False
        self._emit(outbound)

    def apply_override(self, signal_id: str, value: Any) -> dict[str, Any]:
        record = {"id": signal_id, "value": value, "active": True, "timestamp": self._now_ms()}
        with self._lock:
            self._overrides[signal_id] = record
        redis_store.set_json(f"simulation:override:{signal_id}", record)
        self._record_change("override", record)
        return {"success": True}

    def remove_override(self, signal_id: str) -> dict[str, Any]:
        with self._lock:
            self._overrides.pop(signal_id, None)
        redis_store.set_json(f"simulation:override:{signal_id}", {"id": signal_id, "active": False, "timestamp": self._now_ms()})
        self._record_change("override_remove", {"id": signal_id})
        return {"success": True}

    def get_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for key in self._live_signal_keys():
            signal = redis_store.get_json(key, default=None)
            if not isinstance(signal, dict):
                continue
            signal_id = str(signal.get("id") or "")
            if not signal_id:
                continue
            override = self._overrides.get(signal_id)
            if override and override.get("active"):
                state[signal_id] = {"value": override.get("value"), "simulated": True, "timestamp": signal.get("timestamp"), "source": signal.get("source")}
            else:
                state[signal_id] = {"value": signal.get("value"), "simulated": False, "timestamp": signal.get("timestamp"), "source": signal.get("source")}
        return state

    def register_ai_connector(self, connector_id: str, endpoint: str, api_key: str | None = None) -> dict[str, Any]:
        self._ai_connectors[connector_id] = {"id": connector_id, "endpoint": endpoint, "apiKey": api_key}
        return {"success": True}

    def _build_ai_context(self, limit: int = 75) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for key in self._live_signal_keys():
            signal = redis_store.get_json(key, default=None)
            if isinstance(signal, dict):
                rows.append(signal)
        rows.sort(key=lambda item: int(item.get("timestamp") or 0), reverse=True)
        return {"signals": rows[:limit], "overrides": list(self._overrides.values()), "timestamp": self._now_ms()}

    def ai_query(self, connector_id: str, prompt: str) -> dict[str, Any]:
        connector = self._ai_connectors.get(connector_id)
        if not connector:
            raise ValueError("AI connector not found")
        context = self._build_ai_context(limit=75)
        if not context["signals"]:
            return {"response": {"message": "No valid live data available"}, "suggestedAction": None, "contextPreview": []}
        headers: dict[str, str] = {"Content-Type": "application/json"}
        api_key = str(connector.get("apiKey") or "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        endpoint = str(connector.get("endpoint") or "").strip()
        if endpoint in {"mock://ai", "demo://ai"}:
            payload = {
                "message": f"Demo AI response for: {prompt}",
                "command": {"id": "pump.speed", "value": 72.5},
            }
        else:
            response = requests.post(
                endpoint,
                json={"prompt": prompt, "context": context, "mode": "simulation"},
                headers=headers,
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
        suggested = payload.get("command") if isinstance(payload, dict) else None
        self._record_change("ai_action", {"prompt": prompt, "response": payload})
        return {"response": payload, "suggestedAction": suggested, "contextPreview": context["signals"][:5]}

    def add_watch_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        rule_id = str(rule.get("id") or "").strip() or str(uuid4())
        self._watch_rules[rule_id] = {"id": rule_id, "tag": str(rule.get("tag") or ""), "condition": str(rule.get("condition") or ">"), "value": rule.get("value")}
        return {"success": True, "id": rule_id}

    def check_watch_rules(self) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for rule in self._watch_rules.values():
            signal = redis_store.get_json(f"simulation:live:{rule['tag']}", default=None)
            if not isinstance(signal, dict):
                continue
            value = signal.get("value")
            threshold = rule.get("value")
            triggered = False
            try:
                if rule["condition"] == ">" and float(value) > float(threshold):
                    triggered = True
                if rule["condition"] == "<" and float(value) < float(threshold):
                    triggered = True
                if rule["condition"] == "=" and str(value) == str(threshold):
                    triggered = True
            except Exception:
                triggered = False
            if triggered:
                alerts.append({"tag": rule["tag"], "value": value, "rule": rule})
        return alerts

    def changelog(self) -> list[dict[str, Any]]:
        return redis_store.get_json_list("simulation:changelog", limit=100)

    def health(self) -> dict[str, Any]:
        connectors: list[dict[str, Any]] = []
        now = self._now_ms()
        for status in self._connector_status.values():
            last_seen = int(status.last_update or 0)
            latency = max(0, now - last_seen) if last_seen else None
            healthy = status.status == "CONNECTED" and (latency is None or latency <= 15000)
            connectors.append({"id": status.id, "healthy": healthy, "lastSeen": last_seen, "latency": latency})
        return {"overallHealthy": all(item["healthy"] for item in connectors) if connectors else False, "connectors": connectors}

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = {"id": str(uuid4()), **event, "timestamp": self._now_ms()}
        redis_store.append_json_list("simulation:events", payload, max_items=5000)
        self._emit({"event": payload})
        return {"success": True, "event": payload}

    def replay_events(self) -> list[dict[str, Any]]:
        events = redis_store.get_json_list("simulation:events", limit=100)
        events.reverse()
        return events


simulation_live_service = SimulationLiveService()
