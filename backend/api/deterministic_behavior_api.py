from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from fastapi import APIRouter, Body, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute, APIWebSocketRoute
from pydantic import BaseModel, Field

from services.behavior_loader_patch import load_parser_output_into_behavior_layer
from services.deterministic_behavior_service import deterministic_behavior_service


router = APIRouter(tags=["deterministic-behavior"])
logger = logging.getLogger(__name__)


class BehaviorLoadRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    runtime_seed: dict[str, dict[str, Any]] | None = None


class BehaviorRuntimeUpdateRequest(BaseModel):
    updates: dict[str, dict[str, Any]] = Field(default_factory=dict)
    radius: int | None = None


def _normalize_runtime_updates(raw: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], int | None]:
    radius_value = raw.get("radius")
    radius = int(radius_value) if isinstance(radius_value, int) else None

    updates_raw = raw.get("updates")
    candidate_updates: dict[str, Any]
    if isinstance(updates_raw, dict):
        candidate_updates = updates_raw
    else:
        candidate_updates = {k: v for k, v in raw.items() if k not in {"updates", "radius"}}

    normalized: dict[str, dict[str, Any]] = {}
    for tag, patch in candidate_updates.items():
        tag_text = str(tag).strip()
        if not tag_text or not isinstance(patch, dict):
            continue
        normalized_patch = dict(patch)
        if "value" in normalized_patch and "current_value" not in normalized_patch:
            normalized_patch["current_value"] = normalized_patch.pop("value")
        normalized[tag_text] = normalized_patch

    return normalized, radius


class BehaviorWebSocketHub:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = RLock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        with self._lock:
            self._connections.add(websocket)
            if self._loop is None:
                self._loop = asyncio.get_running_loop()
        logger.info("behavior_ws client_connected total_clients=%s", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        with self._lock:
            self._connections.discard(websocket)
            remaining = len(self._connections)
        logger.info("behavior_ws client_disconnected remaining_clients=%s", remaining)

    def has_connections(self) -> bool:
        with self._lock:
            return bool(self._connections)

    def connection_count(self) -> int:
        with self._lock:
            return len(self._connections)

    async def send_full_snapshot(self, websocket: WebSocket) -> None:
        rows = deterministic_behavior_service.get_rows()
        edges = deterministic_behavior_service.get_edges()
        payload = {
            "event": "behavior_snapshot_full",
            "success": True,
            "snapshot_id": rows[0].get("state_snapshot_id") if rows else "snapshot-00000000",
            "rows": rows,
            "updated_rows": rows,
            "edges": edges,
            "changed_tags": [],
            "impacted_tags": [],
            "ignored_tags": [],
            "unknown_tags": [],
            "debug": {
                "source": "initial_snapshot",
            },
            "count": len(rows),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_json(payload)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        with self._lock:
            clients = list(self._connections)

        if not clients:
            return

        dead: list[WebSocket] = []
        for websocket in clients:
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)

        if dead:
            with self._lock:
                for websocket in dead:
                    self._connections.discard(websocket)

    def publish_from_listener(self, event_type: str, payload: dict[str, Any]) -> None:
        with self._lock:
            loop = self._loop
            has_clients = bool(self._connections)

        if loop is None or not has_clients:
            return

        if event_type == "runtime_update":
            message = {
                "event": "behavior_snapshot_partial",
                "success": True,
                "snapshot_id": payload.get("snapshot_id"),
                "rows": payload.get("updated_rows", []),
                "changed_tags": payload.get("changed_tags", []),
                "impacted_tags": payload.get("impacted_tags", []),
                "updated_rows": payload.get("updated_rows", []),
                "ignored_tags": payload.get("ignored_tags", []),
                "unknown_tags": payload.get("unknown_tags", []),
                "tag_remap": payload.get("tag_remap", {}),
                "debug": payload.get("debug", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.info(
                "behavior_ws partial_broadcast queued clients=%s rows=%s changed_tags=%s ignored=%s unknown=%s",
                self.connection_count(),
                len(message.get("updated_rows", [])),
                len(message.get("changed_tags", [])),
                len(message.get("ignored_tags", [])),
                len(message.get("unknown_tags", [])),
            )
        elif event_type == "loaded":
            rows = deterministic_behavior_service.get_rows()
            edges = deterministic_behavior_service.get_edges()
            message = {
                "event": "behavior_snapshot_full",
                "success": True,
                "snapshot_id": payload.get("snapshot_id"),
                "rows": rows,
                "updated_rows": rows,
                "edges": edges,
                "changed_tags": [],
                "impacted_tags": [],
                "ignored_tags": [],
                "unknown_tags": [],
                "debug": {
                    "source": "reload",
                },
                "count": len(rows),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            return

        asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)


behavior_ws_hub = BehaviorWebSocketHub()
behavior_ws_listener_id = deterministic_behavior_service.register_listener(behavior_ws_hub.publish_from_listener)


@router.post("/behavior/load")
def behavior_load(payload: BehaviorLoadRequest) -> dict[str, Any]:
    result = deterministic_behavior_service.load(
        rows=payload.rows,
        edges=payload.edges,
        runtime_seed=payload.runtime_seed,
    )
    logger.info(
        "behavior_api loaded rows=%s edges=%s snapshot_id=%s",
        len(payload.rows),
        len(payload.edges),
        result.get("snapshot_id"),
    )
    return {
        "success": True,
        "message": "Deterministic behavior cache loaded.",
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/behavior/runtime-update")
def behavior_runtime_update(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    updates, radius = _normalize_runtime_updates(payload if isinstance(payload, dict) else {})
    payload_keys = sorted(payload.keys()) if isinstance(payload, dict) else []
    logger.info("behavior_runtime_update_request payload_keys=%s normalized_tags=%s radius=%s", payload_keys, sorted(updates.keys()), radius)
    for tag in sorted(updates.keys()):
        logger.info(
            "behavior_runtime_update_tag tag=%s exists_in_rows=%s exists_in_runtime=%s",
            tag,
            deterministic_behavior_service.has_row_tag(tag),
            deterministic_behavior_service.has_runtime_tag(tag),
        )

    result = deterministic_behavior_service.update_runtime_values(updates=updates, radius=radius)
    logger.info(
        "behavior_runtime_update_result changed_tags=%s impacted_tags=%s ignored_tags=%s unknown_tags=%s remapped=%s updated_rows=%s",
        result.get("changed_tags", []),
        result.get("impacted_tags", []),
        result.get("ignored_tags", []),
        result.get("unknown_tags", []),
        result.get("tag_remap", {}),
        len(result.get("updated_rows", []) or []),
    )
    return {
        "success": True,
        "message": "Deterministic behavior runtime state updated.",
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/behavior/rows")
def behavior_rows(tags: str | None = Query(default=None)) -> dict[str, Any]:
    requested_tags = [item.strip() for item in tags.split(",") if item.strip()] if tags else None
    rows = deterministic_behavior_service.get_rows(requested_tags)
    snapshot_id = rows[0].get("state_snapshot_id") if rows else "snapshot-00000000"
    return {
        "success": True,
        "message": "Deterministic behavior rows fetched.",
        "data": {
            "snapshot_id": snapshot_id,
            "rows": rows,
            "count": len(rows),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/behavior/why/{tag}")
def behavior_why(tag: str, max_depth: int = Query(default=3, ge=1, le=10)) -> dict[str, Any]:
    logger.info("[WHY_CHAIN_DEBUG] api_selected_tag=%s max_depth=%s", tag, max_depth)
    explanation = deterministic_behavior_service.explain_why(tag=tag, max_depth=max_depth)
    logger.info("[WHY_CHAIN_DEBUG] api_response_tag=%s", explanation.get("tag"))
    if str(explanation.get("tag") or "") != str(tag or ""):
        logger.error(
            "[WHY_CHAIN_DEBUG] selected_tag_mismatch requested=%s response=%s",
            tag,
            explanation.get("tag"),
        )
    return {
        "success": True,
        "message": "Deterministic behavior why-trace generated.",
        "data": explanation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.websocket("/ws/behavior")
async def behavior_stream(websocket: WebSocket) -> None:
    await behavior_ws_hub.connect(websocket)
    try:
        await behavior_ws_hub.send_full_snapshot(websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await behavior_ws_hub.disconnect(websocket)
    except Exception:
        logger.exception("behavior_ws stream_error")
        await behavior_ws_hub.disconnect(websocket)
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/debug/behavior-check")
def behavior_check(request: Request) -> dict[str, Any]:
    app_routes = list(request.app.routes)

    http_route_map: dict[str, set[str]] = {}
    websocket_paths: set[str] = set()
    for route in app_routes:
        if isinstance(route, APIRoute):
            methods = {method.upper() for method in (route.methods or set())}
            existing = http_route_map.get(route.path, set())
            http_route_map[route.path] = existing | methods
        elif isinstance(route, APIWebSocketRoute):
            websocket_paths.add(route.path)

    rows = deterministic_behavior_service.get_rows()
    known_tag = rows[0].get("tag") if rows else ""

    why_ok = False
    if known_tag:
        why_result = deterministic_behavior_service.explain_why(str(known_tag), max_depth=2)
        why_ok = isinstance(why_result, dict) and str(why_result.get("tag") or "") == str(known_tag)
    else:
        why_result = deterministic_behavior_service.explain_why("__unknown__", max_depth=2)
        why_ok = isinstance(why_result, dict)

    runtime_probe = deterministic_behavior_service.update_runtime_values({})
    parser_loader_present = callable(load_parser_output_into_behavior_layer)

    payload = {
        "behavior_routes_registered": (
            "/api/behavior/load" in http_route_map
            and "POST" in http_route_map.get("/api/behavior/load", set())
            and "/api/behavior/runtime-update" in http_route_map
            and "POST" in http_route_map.get("/api/behavior/runtime-update", set())
            and "/api/behavior/rows" in http_route_map
            and "GET" in http_route_map.get("/api/behavior/rows", set())
        ),
        "rows_endpoint_ok": isinstance(rows, list),
        "why_endpoint_ok": why_ok,
        "runtime_update_endpoint_ok": isinstance(runtime_probe, dict),
        "websocket_route_configured": "/api/ws/behavior" in websocket_paths,
        "parser_behavior_loader_present": parser_loader_present,
        "rows_loaded_count": deterministic_behavior_service.get_rows_loaded_count(),
        "listener_count": deterministic_behavior_service.get_listener_count(),
    }
    return payload


@router.get("/debug/behavior-tag/{tag}")
def behavior_tag_debug(tag: str) -> dict[str, Any]:
    exists_in_rows = deterministic_behavior_service.has_row_tag(tag)
    exists_in_runtime = deterministic_behavior_service.has_runtime_tag(tag)
    row_preview = deterministic_behavior_service.get_row_preview(tag)
    return {
        "tag": tag,
        "exists_in_rows": exists_in_rows,
        "exists_in_runtime": exists_in_runtime,
        "row_preview": row_preview,
    }


@router.get("/debug/behavior-summary")
def behavior_summary_debug() -> dict[str, Any]:
    return {
        "row_count": deterministic_behavior_service.get_rows_loaded_count(),
        "runtime_count": deterministic_behavior_service.get_runtime_values_count(),
        "sample_tags": deterministic_behavior_service.get_sample_tags(limit=10),
    }
