from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.database import redis_store


AUDIT_KEY = "audit:events"


class AuditLogger:
    def record(self, event_type: str, actor: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "event_type": event_type,
            "actor": actor,
            "details": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        redis_store.append_json_list(AUDIT_KEY, payload, max_items=5000)
        return payload

    def list(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = redis_store.get_json_list(AUDIT_KEY, limit=max(1, limit))
        output: list[dict[str, Any]] = []
        for row in rows:
            if isinstance(row, dict):
                output.append(row)
        return output


audit_logger = AuditLogger()
