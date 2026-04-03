from __future__ import annotations

import asyncio
import time
from threading import RLock
from typing import Any
from uuid import uuid4

from core.database import redis_store


class SimulationLiveService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._overrides: dict[str, dict[str, Any]] = {}
        self._watch_rules: dict[str, dict[str, Any]] = {}
        self._change_log: list[dict[str, Any]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

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
        override = self._overrides.get(signal_id)
        if override and override.get("active"):
            payload["value"] = override.get("value")
            payload["simulated"] = True
        else:
            payload["simulated"] = False

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

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = {"id": str(uuid4()), **event, "timestamp": self._now_ms()}
        redis_store.append_json_list("simulation:events", payload, max_items=5000)
        return {"success": True, "event": payload}


simulation_live_service = SimulationLiveService()
