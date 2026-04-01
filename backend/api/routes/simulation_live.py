from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from services.simulation_live_service import simulation_live_service

router = APIRouter(prefix="/simulation", tags=["simulation-live"])


@router.on_event("startup")
async def _set_loop() -> None:
    simulation_live_service.set_event_loop(asyncio.get_running_loop())


@router.post("/connectors/test")
def test_connector(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return simulation_live_service.test_connector(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/connectors/activate")
def activate_connector(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return simulation_live_service.activate_connector(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/connectors/status")
def connector_status() -> list[dict[str, Any]]:
    return simulation_live_service.connector_status_list()


@router.post("/connectors/init")
def init_connector(payload: dict[str, Any]) -> dict[str, Any]:
    simulation_live_service.test_connector(payload)
    return simulation_live_service.activate_connector(payload)


@router.post("/signal/publish")
def publish_signal(payload: dict[str, Any]) -> dict[str, Any]:
    simulation_live_service.publish_signal(payload)
    return {"success": True}


@router.post("/override")
def apply_override(payload: dict[str, Any]) -> dict[str, Any]:
    signal_id = str(payload.get("id") or "").strip()
    if not signal_id:
        raise HTTPException(status_code=400, detail="id is required")
    return simulation_live_service.apply_override(signal_id, payload.get("value"))


@router.post("/override/remove")
def remove_override(payload: dict[str, Any]) -> dict[str, Any]:
    signal_id = str(payload.get("id") or "").strip()
    if not signal_id:
        raise HTTPException(status_code=400, detail="id is required")
    return simulation_live_service.remove_override(signal_id)


@router.get("/state")
def get_state() -> dict[str, Any]:
    return simulation_live_service.get_state()


@router.get("/stream")
async def stream_state(request: Request) -> StreamingResponse:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    simulation_live_service.register_sse_queue(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                if "event" in event:
                    yield f"event: system\ndata: {json.dumps(event['event'])}\n\n"
                else:
                    yield f"data: {json.dumps(event)}\n\n"
        finally:
            simulation_live_service.unregister_sse_queue(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})


@router.post("/ai/register")
def register_ai(payload: dict[str, Any]) -> dict[str, Any]:
    connector_id = str(payload.get("id") or "").strip() or "default"
    endpoint = str(payload.get("endpoint") or "").strip()
    if not endpoint:
        raise HTTPException(status_code=400, detail="endpoint is required")
    api_key = payload.get("apiKey")
    return simulation_live_service.register_ai_connector(connector_id, endpoint, api_key if isinstance(api_key, str) else None)


@router.post("/ai/query")
def ai_query(payload: dict[str, Any]) -> dict[str, Any]:
    connector_id = str(payload.get("connectorId") or "default")
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    try:
        return simulation_live_service.ai_query(connector_id, prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ai/apply-action")
def ai_apply_action(payload: dict[str, Any]) -> dict[str, Any]:
    signal_id = str(payload.get("id") or "").strip()
    if not signal_id:
        raise HTTPException(status_code=400, detail="id is required")
    return simulation_live_service.apply_override(signal_id, payload.get("value"))


@router.post("/watch/add")
def watch_add(payload: dict[str, Any]) -> dict[str, Any]:
    return simulation_live_service.add_watch_rule(payload)


@router.get("/watch/check")
def watch_check() -> list[dict[str, Any]]:
    return simulation_live_service.check_watch_rules()


@router.get("/changelog")
def changelog() -> list[dict[str, Any]]:
    return simulation_live_service.changelog()


@router.get("/health")
def health() -> dict[str, Any]:
    return simulation_live_service.health()


@router.post("/event")
def push_event(payload: dict[str, Any]) -> dict[str, Any]:
    return simulation_live_service.append_event(payload)


@router.get("/events/replay")
def events_replay() -> list[dict[str, Any]]:
    return simulation_live_service.replay_events()
