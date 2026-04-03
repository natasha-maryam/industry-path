from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.auto_tag_mapper import auto_tag_mapper
from services.relational_query_engine import relational_query_engine


router = APIRouter(tags=["system-layer-upgrade"])


class AutoMapRequest(BaseModel):
    external_tags: list[str] = Field(default_factory=list)
    threshold: float | None = None


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
