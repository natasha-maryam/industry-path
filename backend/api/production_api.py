from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from core.audit import audit_logger
from core.database import redis_store
from core.metrics import request_metrics_store
from core.models import ConnectorHealthResponse, HealthResponse, RuntimeQueueRequest, ScriptQueueRequest
from core.rate_limit import enforce_rate_limit
from core.security import AuthContext, get_auth_context, require_admin
from core.tasks import enqueue_runtime_update, enqueue_script
from services.connector_manager import connector_manager


router = APIRouter(prefix="/production", tags=["production"])


def _rate_limit_dependency(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    enforce_rate_limit(context.user_id, route_scope="production")
    return context


@router.post("/runtime-update")
def queue_runtime_update(
    payload: RuntimeQueueRequest,
    context: AuthContext = Depends(_rate_limit_dependency),
) -> dict[str, Any]:
    queued = enqueue_runtime_update(payload.project_id, payload.updates)
    audit_logger.record(
        event_type="runtime_update_queued",
        actor=context.user_id,
        details={
            "project_id": payload.project_id,
            "tags": sorted(payload.updates.keys()),
            "task": queued,
        },
    )
    return {
        "success": True,
        "message": "Runtime update accepted.",
        "data": queued,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/script")
def queue_script(
    payload: ScriptQueueRequest,
    context: AuthContext = Depends(require_admin),
) -> dict[str, Any]:
    enforce_rate_limit(context.user_id, route_scope="production-script")
    queued = enqueue_script(payload.script)
    audit_logger.record(
        event_type="script_queued",
        actor=context.user_id,
        details={
            "project_id": payload.project_id,
            "task": queued,
            "internal_only": True,
        },
    )
    return {
        "success": True,
        "message": "Script execution queued (internal/admin).",
        "data": queued,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/connectors/health", response_model=ConnectorHealthResponse)
def get_connector_health(context: AuthContext = Depends(_rate_limit_dependency)) -> ConnectorHealthResponse:
    _ = context
    return ConnectorHealthResponse(connectors=connector_manager.health())


@router.get("/audit")
def get_audit_logs(limit: int = 200, context: AuthContext = Depends(require_admin)) -> dict[str, Any]:
    enforce_rate_limit(context.user_id, route_scope="production-audit")
    rows = audit_logger.list(limit=max(1, min(limit, 1000)))
    return {
        "success": True,
        "message": "Audit log entries fetched.",
        "data": {
            "events": rows,
            "count": len(rows),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health", response_model=HealthResponse)
def production_health(context: AuthContext = Depends(get_auth_context)) -> HealthResponse:
    _ = context
    connector_health = connector_manager.health()
    healthy_connectors = sum(1 for item in connector_health if item.get("healthy"))

    payload = {
        "status": "ok",
        "services": {
            "redis": {
                "enabled": redis_store.is_redis_enabled,
            },
            "connectors": {
                "healthy": healthy_connectors,
                "total": len(connector_health),
            },
            "metrics": request_metrics_store.snapshot(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return HealthResponse(**payload)


@router.get("/metrics")
def get_metrics(context: AuthContext = Depends(require_admin)) -> dict[str, Any]:
    enforce_rate_limit(context.user_id, route_scope="production-metrics")
    return {
        "success": True,
        "message": "Request metrics snapshot.",
        "data": request_metrics_store.snapshot(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
