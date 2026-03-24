from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


class VersionedViewsService:
    """Project-scoped saved engineering views and snapshot versions.

    SQLite is used for local development persistence. The public methods are intentionally
    repository-like so persistence can migrate to PostgreSQL later with minimal API changes.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        default_db_path = Path(__file__).resolve().parents[2] / "storage" / "views" / "versioned_views.db"
        self._db_path = db_path or default_db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS views (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    query TEXT,
                    script TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS view_versions (
                    id TEXT PRIMARY KEY,
                    view_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(view_id) REFERENCES views(id)
                )
                """
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_views_project ON views(project_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_view_versions_view ON view_versions(view_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_view_versions_project ON view_versions(project_id)")

    def create_view(self, project_id: str, name: str, query: str | None = None, script: str | None = None) -> dict[str, Any]:
        project = (project_id or "").strip()
        view_name = (name or "").strip()
        if not project:
            raise ValueError("project_id is required")
        if not view_name:
            raise ValueError("name is required")

        payload = {
            "id": str(uuid4()),
            "project_id": project,
            "name": view_name,
            "query": (query or "").strip() or None,
            "script": (script or "").strip() or None,
            "created_at": self._now(),
        }
        with self._lock:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO views (id, project_id, name, query, script, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["id"],
                        payload["project_id"],
                        payload["name"],
                        payload["query"],
                        payload["script"],
                        payload["created_at"],
                    ),
                )
        return payload

    def list_views(self, project_id: str) -> list[dict[str, Any]]:
        project = (project_id or "").strip()
        if not project:
            raise ValueError("project_id is required")

        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, project_id, name, query, script, created_at
                FROM views
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_view(self, view_id: str) -> dict[str, Any] | None:
        key = (view_id or "").strip()
        if not key:
            raise ValueError("view_id is required")

        with self._lock:
            row = self._conn.execute(
                """
                SELECT id, project_id, name, query, script, created_at
                FROM views
                WHERE id = ?
                """,
                (key,),
            ).fetchone()
        return dict(row) if row else None

    def create_version(self, view_id: str, snapshot: Any, notes: str | None = None) -> dict[str, Any]:
        key = (view_id or "").strip()
        if not key:
            raise ValueError("view_id is required")

        view = self.get_view(key)
        if view is None:
            raise ValueError(f"view not found: {view_id}")

        payload = {
            "id": str(uuid4()),
            "view_id": key,
            "project_id": str(view["project_id"]),
            "snapshot_json": json.dumps(snapshot, default=str),
            "notes": (notes or "").strip() or None,
            "created_at": self._now(),
        }
        with self._lock:
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO view_versions (id, view_id, project_id, snapshot_json, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["id"],
                        payload["view_id"],
                        payload["project_id"],
                        payload["snapshot_json"],
                        payload["notes"],
                        payload["created_at"],
                    ),
                )
        return {
            "id": payload["id"],
            "view_id": payload["view_id"],
            "project_id": payload["project_id"],
            "notes": payload["notes"],
            "created_at": payload["created_at"],
        }

    def list_versions(self, view_id: str) -> list[dict[str, Any]]:
        key = (view_id or "").strip()
        if not key:
            raise ValueError("view_id is required")

        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, view_id, project_id, notes, created_at
                FROM view_versions
                WHERE view_id = ?
                ORDER BY created_at DESC
                """,
                (key,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_version(self, version_id: str) -> dict[str, Any] | None:
        key = (version_id or "").strip()
        if not key:
            raise ValueError("version_id is required")

        with self._lock:
            row = self._conn.execute(
                """
                SELECT id, view_id, project_id, snapshot_json, notes, created_at
                FROM view_versions
                WHERE id = ?
                """,
                (key,),
            ).fetchone()
        if not row:
            return None

        payload = dict(row)
        snapshot_raw = payload.pop("snapshot_json", "{}")
        payload["snapshot"] = json.loads(snapshot_raw) if snapshot_raw else {}
        return payload

    @staticmethod
    def _snapshot_rows(snapshot: Any) -> list[dict[str, Any]]:
        if isinstance(snapshot, dict):
            rows = snapshot.get("rows")
            if isinstance(rows, list):
                return [item for item in rows if isinstance(item, dict)]
        if isinstance(snapshot, list):
            return [item for item in snapshot if isinstance(item, dict)]
        return []

    @staticmethod
    def _row_identity(row: dict[str, Any]) -> str:
        tag = str(row.get("tag") or "").strip()
        if tag:
            return tag
        row_id = str(row.get("id") or "").strip()
        if row_id:
            return row_id
        return ""

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, list):
            return [VersionedViewsService._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: VersionedViewsService._normalize_value(val) for key, val in value.items()}
        return value

    def diff_versions(self, before_version_id: str, after_version_id: str) -> dict[str, Any]:
        before_version = self.get_version(before_version_id)
        after_version = self.get_version(after_version_id)
        if before_version is None:
            raise ValueError(f"before version not found: {before_version_id}")
        if after_version is None:
            raise ValueError(f"after version not found: {after_version_id}")

        before_rows = self._snapshot_rows(before_version.get("snapshot"))
        after_rows = self._snapshot_rows(after_version.get("snapshot"))

        before_map = {self._row_identity(row): row for row in before_rows if self._row_identity(row)}
        after_map = {self._row_identity(row): row for row in after_rows if self._row_identity(row)}

        all_keys = sorted(set(before_map.keys()) | set(after_map.keys()))
        added: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        changed: list[dict[str, Any]] = []

        for key in all_keys:
            left = before_map.get(key)
            right = after_map.get(key)
            if left is None and right is not None:
                added.append({"tag": key, "after": right})
                continue
            if right is None and left is not None:
                removed.append({"tag": key, "before": left})
                continue
            if left is None or right is None:
                continue

            left_norm = self._normalize_value(left)
            right_norm = self._normalize_value(right)
            if left_norm == right_norm:
                continue

            field_changes: list[dict[str, Any]] = []
            fields = sorted(set(left_norm.keys()) | set(right_norm.keys()))
            for field in fields:
                left_value = left_norm.get(field)
                right_value = right_norm.get(field)
                if left_value != right_value:
                    field_changes.append(
                        {
                            "field": field,
                            "before": left_value,
                            "after": right_value,
                        }
                    )

            changed.append(
                {
                    "tag": key,
                    "fields": field_changes,
                    "before": left,
                    "after": right,
                }
            )

        return {
            "before_version_id": before_version_id,
            "after_version_id": after_version_id,
            "summary": {
                "added": len(added),
                "removed": len(removed),
                "changed": len(changed),
            },
            "added": added,
            "removed": removed,
            "changed": changed,
        }


versioned_views_service = VersionedViewsService()
