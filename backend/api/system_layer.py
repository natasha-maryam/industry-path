from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.uns_core import uns_core


router = APIRouter(tags=["uns-system-layer"])


class UNSLoadRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


class UNSRuntimeUpdateRequest(BaseModel):
    updates: dict[str, dict[str, Any]] = Field(default_factory=dict)


class UNSMapRequest(BaseModel):
    tag: str
    mapping: dict[str, Any] = Field(default_factory=dict)


class UNSQueryRequest(BaseModel):
    query: str


class UNSScriptRequest(BaseModel):
    script: str


class UNSConnectorRequest(BaseModel):
    connector_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UNSWebSocketHub:
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

    def disconnect(self, websocket: WebSocket) -> None:
        with self._lock:
            self._connections.discard(websocket)

    async def send_initial(self, websocket: WebSocket) -> None:
        payload = {
            "event": "uns_snapshot_full",
            "rows": uns_core.get_rows(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_json(payload)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        with self._lock:
            clients = list(self._connections)

        if not clients:
            return

        dead: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_json(payload)
            except Exception:
                dead.append(client)

        if dead:
            with self._lock:
                for client in dead:
                    self._connections.discard(client)

    def publish(self, event: str, payload: dict[str, Any]) -> None:
        with self._lock:
            loop = self._loop
            has_clients = bool(self._connections)

        if loop is None or not has_clients:
            return

        message = {
            **payload,
            "event": payload.get("event") or event,
        }
        asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)


uns_ws_hub = UNSWebSocketHub()
uns_ws_listener_id = uns_core.register_listener(uns_ws_hub.publish)


@router.post("/uns/load")
def uns_load(payload: UNSLoadRequest) -> dict[str, Any]:
    try:
        result = uns_core.load_model(payload.rows, payload.edges)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "UNS model loaded.",
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/uns/runtime-update")
def uns_runtime_update(payload: UNSRuntimeUpdateRequest) -> dict[str, Any]:
    result = uns_core.update_runtime(payload.updates)
    return {
        "success": True,
        "message": "UNS runtime updated.",
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/uns/rows")
def uns_rows() -> dict[str, Any]:
    rows = uns_core.get_rows()
    return {
        "success": True,
        "message": "UNS rows fetched.",
        "data": {
            "rows": rows,
            "count": len(rows),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/uns/map")
def uns_map(payload: UNSMapRequest) -> dict[str, Any]:
    try:
        mapped = uns_core.map_tag(payload.tag, payload.mapping)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "UNS tag mapping updated.",
        "data": mapped,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/uns/query")
def uns_query(payload: UNSQueryRequest) -> dict[str, Any]:
    try:
        rows = uns_core.query(payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "UNS query executed.",
        "data": {
            "rows": rows,
            "count": len(rows),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/uns/script")
def uns_script(payload: UNSScriptRequest) -> dict[str, Any]:
    try:
        result = uns_core.run_script(payload.script)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "UNS script executed.",
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/uns/connector")
def uns_connector(payload: UNSConnectorRequest) -> dict[str, Any]:
    try:
        result = uns_core.set_connector(payload.connector_type, payload.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "Connector metadata updated.",
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/uns/connectors")
def uns_connectors() -> dict[str, Any]:
    connectors = uns_core.get_connectors()
    return {
        "success": True,
        "message": "Connector metadata fetched.",
        "data": connectors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.websocket("/ws/uns")
async def uns_stream(websocket: WebSocket) -> None:
    await uns_ws_hub.connect(websocket)
    try:
        await uns_ws_hub.send_initial(websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        uns_ws_hub.disconnect(websocket)
    except Exception:
        uns_ws_hub.disconnect(websocket)
        try:
            await websocket.close()
        except Exception:
            pass
