from __future__ import annotations

import ast
import sqlite3
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Mapping


UNSListener = Callable[[str, dict[str, Any]], None]


@dataclass(slots=True)
class UNSRow:
    tag: str
    type: str = "unknown"
    subtype: str | None = None
    equipment: str | None = None
    current_value: str | None = None
    state: str | None = None
    setpoint: str | None = None
    mode: str | None = None
    controls: list[str] = field(default_factory=list)
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    behavior_card: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "type": self.type,
            "subtype": self.subtype,
            "equipment": self.equipment,
            "current_value": self.current_value,
            "state": self.state,
            "setpoint": self.setpoint,
            "mode": self.mode,
            "controls": list(self.controls),
            "upstream": list(self.upstream),
            "downstream": list(self.downstream),
            "behavior_card": self.behavior_card,
        }


class UNSCore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._rows_by_tag: dict[str, UNSRow] = {}
        self._edges: list[dict[str, Any]] = []
        self._mappings: dict[str, dict[str, Any]] = {}
        self._connectors: dict[str, dict[str, Any]] = {}
        self._listeners: dict[str, UNSListener] = {}
        self._listener_counter = 0
        self._revision = 0

        self._db = sqlite3.connect(":memory:", check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_db()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _init_db(self) -> None:
        with self._db:
            self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS uns_rows (
                    tag TEXT PRIMARY KEY,
                    type TEXT,
                    subtype TEXT,
                    equipment TEXT,
                    current_value TEXT,
                    state TEXT,
                    setpoint TEXT,
                    mode TEXT,
                    controls_json TEXT,
                    upstream_json TEXT,
                    downstream_json TEXT,
                    behavior_card TEXT
                )
                """
            )

    @staticmethod
    def _to_row(raw: Mapping[str, Any]) -> UNSRow:
        tag = str(raw.get("tag") or "").strip()
        if not tag:
            raise ValueError("Row tag is required.")
        return UNSRow(
            tag=tag,
            type=str(raw.get("type") or "unknown"),
            subtype=(str(raw.get("subtype")) if raw.get("subtype") is not None else None),
            equipment=(str(raw.get("equipment")) if raw.get("equipment") is not None else None),
            current_value=(str(raw.get("current_value")) if raw.get("current_value") is not None else None),
            state=(str(raw.get("state")) if raw.get("state") is not None else None),
            setpoint=(str(raw.get("setpoint")) if raw.get("setpoint") is not None else None),
            mode=(str(raw.get("mode")) if raw.get("mode") is not None else None),
            controls=[str(item) for item in (raw.get("controls") or []) if str(item).strip()],
            upstream=[str(item) for item in (raw.get("upstream") or []) if str(item).strip()],
            downstream=[str(item) for item in (raw.get("downstream") or []) if str(item).strip()],
            behavior_card=(str(raw.get("behavior_card")) if raw.get("behavior_card") is not None else None),
        )

    @staticmethod
    def _json_list(value: list[str]) -> str:
        escaped = [item.replace('"', "\\\"") for item in value]
        return "[" + ",".join(f'"{item}"' for item in escaped) + "]"

    def _refresh_sql_table_locked(self) -> None:
        with self._db:
            self._db.execute("DELETE FROM uns_rows")
            for row in self._rows_by_tag.values():
                self._db.execute(
                    """
                    INSERT INTO uns_rows (
                        tag, type, subtype, equipment, current_value, state, setpoint, mode,
                        controls_json, upstream_json, downstream_json, behavior_card
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row.tag,
                        row.type,
                        row.subtype,
                        row.equipment,
                        row.current_value,
                        row.state,
                        row.setpoint,
                        row.mode,
                        self._json_list(row.controls),
                        self._json_list(row.upstream),
                        self._json_list(row.downstream),
                        row.behavior_card,
                    ),
                )

    def _notify(self, event: str, payload: dict[str, Any]) -> None:
        listeners = list(self._listeners.values())
        for listener in listeners:
            try:
                listener(event, payload)
            except Exception:
                continue

    def register_listener(self, listener: UNSListener) -> str:
        with self._lock:
            self._listener_counter += 1
            listener_id = f"uns-listener-{self._listener_counter:06d}"
            self._listeners[listener_id] = listener
            return listener_id

    def unregister_listener(self, listener_id: str) -> None:
        with self._lock:
            self._listeners.pop(listener_id, None)

    def load_model(self, rows: list[Mapping[str, Any]], edges: list[Mapping[str, Any]]) -> dict[str, Any]:
        with self._lock:
            normalized_rows = [self._to_row(row) for row in rows]
            self._rows_by_tag = {row.tag: row for row in normalized_rows}
            self._edges = [dict(edge) for edge in edges]
            self._revision += 1
            self._refresh_sql_table_locked()
            payload = {
                "revision": self._revision,
                "rows": len(self._rows_by_tag),
                "edges": len(self._edges),
                "timestamp": self._utc_now(),
            }
        self._notify(
            "uns_snapshot_full",
            {
                "event": "uns_snapshot_full",
                "revision": payload["revision"],
                "rows": self.get_rows(),
                "timestamp": payload["timestamp"],
            },
        )
        return payload

    def update_runtime(self, updates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        changed_rows: list[dict[str, Any]] = []
        changed_tags: list[str] = []

        with self._lock:
            for tag, patch in updates.items():
                row = self._rows_by_tag.get(tag)
                if row is None:
                    continue

                changed = False
                for key in ("current_value", "state", "setpoint", "mode", "type", "subtype", "equipment", "behavior_card"):
                    if key in patch:
                        next_value = patch.get(key)
                        next_normalized = None if next_value is None else str(next_value)
                        if getattr(row, key) != next_normalized:
                            setattr(row, key, next_normalized)
                            changed = True

                for relation_key in ("controls", "upstream", "downstream"):
                    if relation_key in patch and isinstance(patch.get(relation_key), list):
                        next_values = [str(item) for item in patch.get(relation_key, []) if str(item).strip()]
                        if getattr(row, relation_key) != next_values:
                            setattr(row, relation_key, next_values)
                            changed = True

                if changed:
                    changed_tags.append(tag)
                    changed_rows.append(row.as_dict())

            if changed_rows:
                self._revision += 1
                self._refresh_sql_table_locked()
            revision = self._revision

        if changed_rows:
            self._notify(
                "uns_snapshot_partial",
                {
                    "event": "uns_snapshot_partial",
                    "revision": revision,
                    "changed_tags": sorted(changed_tags),
                    "updated_rows": changed_rows,
                    "timestamp": self._utc_now(),
                },
            )

        return {
            "revision": revision,
            "changed_tags": sorted(changed_tags),
            "updated_rows": changed_rows,
            "timestamp": self._utc_now(),
        }

    def get_rows(self) -> list[dict[str, Any]]:
        with self._lock:
            return [row.as_dict() for row in sorted(self._rows_by_tag.values(), key=lambda item: item.tag)]

    def get_edges(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._edges]

    def map_tag(self, tag: str, mapping: Mapping[str, Any]) -> dict[str, Any]:
        normalized_tag = str(tag).strip()
        if not normalized_tag:
            raise ValueError("Tag must not be empty.")
        with self._lock:
            self._mappings[normalized_tag] = {
                **dict(mapping),
                "tag": normalized_tag,
                "updated_at": self._utc_now(),
            }
            mapped = dict(self._mappings[normalized_tag])
        self._notify(
            "uns_mapping",
            {
                "event": "uns_mapping",
                "mapping": mapped,
                "timestamp": self._utc_now(),
            },
        )
        return mapped

    def get_mappings(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {tag: dict(payload) for tag, payload in self._mappings.items()}

    def set_connector(self, connector_type: str, metadata: Mapping[str, Any]) -> dict[str, Any]:
        normalized = str(connector_type).strip().lower()
        if normalized not in {"opcua", "mqtt", "api"}:
            raise ValueError("connector_type must be one of: opcua, mqtt, api")

        with self._lock:
            payload = {
                "type": normalized,
                **dict(metadata),
                "updated_at": self._utc_now(),
            }
            self._connectors[normalized] = payload
            return dict(payload)

    def get_connectors(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {name: dict(payload) for name, payload in self._connectors.items()}

    def query(self, sql: str) -> list[dict[str, Any]]:
        statement = (sql or "").strip()
        if not statement:
            raise ValueError("Query must not be empty.")

        lowered = statement.lower()
        if not lowered.startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

        if ";" in statement.rstrip(";"):
            raise ValueError("Multiple statements are not allowed.")

        aliased_statement = re.sub(r"\bFROM\s+tags\b", "FROM uns_rows", statement, flags=re.IGNORECASE)
        aliased_statement = re.sub(r"\bJOIN\s+tags\b", "JOIN uns_rows", aliased_statement, flags=re.IGNORECASE)

        with self._lock:
            try:
                cursor = self._db.execute(aliased_statement)
                rows = cursor.fetchall()
                return [dict(item) for item in rows]
            except sqlite3.Error as exc:
                raise ValueError(f"Invalid UNS query: {exc}") from exc

    def run_script(self, script: str) -> dict[str, Any]:
        source = (script or "").strip()
        if not source:
            raise ValueError("Script must not be empty.")

        tree = ast.parse(source, mode="exec")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.With, ast.AsyncWith, ast.Try, ast.Lambda)):
                raise ValueError("Script contains unsupported statement.")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "compile", "open", "__import__"}:
                raise ValueError("Script contains blocked call.")

        # TODO(security): Replace this internal/dev sandbox with a hardened policy engine before production exposure.
        sandbox_locals: dict[str, Any] = {}
        sandbox_globals: dict[str, Any] = {
            "__builtins__": {
                "len": len,
                "min": min,
                "max": max,
                "sum": sum,
                "sorted": sorted,
                "round": round,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
            },
            "get_rows": self.get_rows,
            "query": self.query,
            "map_tag": self.map_tag,
            "update_runtime": self.update_runtime,
            "get_mappings": self.get_mappings,
            "set_connector": self.set_connector,
            "get_connectors": self.get_connectors,
            "rows": self.get_rows(),
        }

        try:
            exec(compile(tree, filename="<uns-script>", mode="exec"), sandbox_globals, sandbox_locals)
        except Exception as exc:
            raise ValueError(f"Script execution failed: {exc}") from exc
        result = sandbox_locals.get("result")

        return {
            "result": result,
            "timestamp": self._utc_now(),
        }


uns_core = UNSCore()
