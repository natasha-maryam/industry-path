from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException

from services.simulation_live_service import simulation_live_service

router = APIRouter(prefix="/simulation", tags=["simulation-live"])


@router.on_event("startup")
async def _set_loop() -> None:
    simulation_live_service.set_event_loop(asyncio.get_running_loop())


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


@router.post("/watch/add")
def watch_add(payload: dict[str, Any]) -> dict[str, Any]:
    return simulation_live_service.add_watch_rule(payload)


@router.get("/watch/check")
def watch_check() -> list[dict[str, Any]]:
    return simulation_live_service.check_watch_rules()


@router.post("/event")
def push_event(payload: dict[str, Any]) -> dict[str, Any]:
    return simulation_live_service.append_event(payload)
