from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.auto_tag_mapper import auto_tag_mapper
from services.live_connectors import live_connector_manager
from services.relational_query_engine import relational_query_engine


router = APIRouter(tags=["system-layer-upgrade"])


class OPCUAConnectRequest(BaseModel):
    endpoint: str
    security_policy: str | None = None
    auth_mode: str | None = None
    username: str | None = None


class MQTTConnectRequest(BaseModel):
    host: str
    port: int = 1883
    client_id: str | None = None
    topic: str | None = None


class APIConnectRequest(BaseModel):
    endpoint: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)


class AutoMapRequest(BaseModel):
    external_tags: list[str] = Field(default_factory=list)
    threshold: float | None = None


@router.post("/system-layer/connect/opcua")
def connect_opcua(payload: OPCUAConnectRequest) -> dict[str, Any]:
    if not payload.endpoint.strip():
        raise HTTPException(status_code=400, detail="OPC UA endpoint is required")
    try:
        data = live_connector_manager.configure_opcua(
            endpoint=payload.endpoint,
            security_policy=payload.security_policy,
            auth_mode=payload.auth_mode,
            username=payload.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "OPC UA connector configured.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/system-layer/connect/mqtt")
def connect_mqtt(payload: MQTTConnectRequest) -> dict[str, Any]:
    if not payload.host.strip():
        raise HTTPException(status_code=400, detail="MQTT host is required")
    try:
        data = live_connector_manager.configure_mqtt(
            host=payload.host,
            port=payload.port,
            client_id=payload.client_id,
            topic=payload.topic,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "MQTT connector configured.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/system-layer/connect/api")
def connect_api(payload: APIConnectRequest) -> dict[str, Any]:
    if not payload.endpoint.strip():
        raise HTTPException(status_code=400, detail="API endpoint is required")
    try:
        data = live_connector_manager.configure_api(
            endpoint=payload.endpoint,
            method=payload.method,
            headers=payload.headers,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "API connector configured.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/system-layer/auto-map")
def auto_map(payload: AutoMapRequest) -> dict[str, Any]:
    if not payload.external_tags:
        raise HTTPException(status_code=400, detail="external_tags must not be empty")
    data = auto_tag_mapper.auto_map(payload.external_tags, threshold=payload.threshold)
    return {
        "success": True,
        "message": "Auto tag mapping completed.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system-layer/trace/{tag}")
def system_trace(tag: str, project_id: str | None = Query(default=None), max_depth: int = Query(default=6, ge=1, le=12)) -> dict[str, Any]:
    if not tag.strip():
        raise HTTPException(status_code=400, detail="tag is required")
    try:
        data = relational_query_engine.trace(tag=tag, project_id=project_id, max_depth=max_depth)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not isinstance(data, dict):
        data = {"tag": tag, "project_id": project_id, "path": [], "steps": []}

    return {
        "success": True,
        "message": "Relational trace completed.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system-layer/loops")
def system_loops(project_id: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    data = relational_query_engine.find_loops(project_id=project_id, limit=limit)
    if not isinstance(data, dict):
        data = {"loops": [], "count": 0}
    return {
        "success": True,
        "message": "Loop analysis completed.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/system-layer/bottlenecks")
def system_bottlenecks(project_id: str | None = Query(default=None), limit: int = Query(default=10, ge=1, le=100)) -> dict[str, Any]:
    data = relational_query_engine.bottlenecks(project_id=project_id, limit=limit)
    if not isinstance(data, dict):
        data = {"bottlenecks": [], "count": 0}
    return {
        "success": True,
        "message": "Bottleneck analysis completed.",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
