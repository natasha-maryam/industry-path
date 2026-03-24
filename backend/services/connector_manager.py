from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.uns_core import uns_core


class ConnectorManager:
    def health(self) -> list[dict[str, Any]]:
        connectors = uns_core.get_connectors()
        response: list[dict[str, Any]] = []

        for connector_type in ("opcua", "mqtt", "api"):
            payload = connectors.get(connector_type)
            if not payload:
                response.append(
                    {
                        "connector_type": connector_type,
                        "configured": False,
                        "healthy": False,
                        "message": "Not configured",
                        "updated_at": None,
                        "metadata": {},
                    }
                )
                continue

            healthy = bool(payload.get("validated", False))
            message = str(payload.get("validation_message") or ("healthy" if healthy else "unhealthy"))
            response.append(
                {
                    "connector_type": connector_type,
                    "configured": True,
                    "healthy": healthy,
                    "message": message,
                    "updated_at": payload.get("updated_at") or datetime.now(timezone.utc).isoformat(),
                    "metadata": {k: v for k, v in payload.items() if k not in {"validation_message", "validated"}},
                }
            )

        return response


connector_manager = ConnectorManager()
