from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.versioned_views import versioned_views_service


router = APIRouter(tags=["views"])


class CreateViewRequest(BaseModel):
    project_id: str
    name: str
    query: str | None = None
    script: str | None = None


class CreateVersionRequest(BaseModel):
    snapshot: dict[str, Any] | list[dict[str, Any]]
    notes: str | None = None


class DiffVersionsRequest(BaseModel):
    before_version_id: str
    after_version_id: str


@router.post("/views")
def create_view(payload: CreateViewRequest) -> dict[str, Any]:
    if not payload.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    try:
        view = versioned_views_service.create_view(
            project_id=payload.project_id,
            name=payload.name,
            query=payload.query,
            script=payload.script,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "View saved.",
        "data": view,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/views")
def list_views(project_id: str = Query(...)) -> dict[str, Any]:
    try:
        views = versioned_views_service.list_views(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "Views fetched.",
        "data": {
            "views": views,
            "count": len(views),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/views/{view_id}/versions")
def create_view_version(view_id: str, payload: CreateVersionRequest) -> dict[str, Any]:
    if not view_id.strip():
        raise HTTPException(status_code=400, detail="view_id is required")
    if isinstance(payload.snapshot, dict) and not payload.snapshot:
        raise HTTPException(status_code=400, detail="snapshot payload must not be empty")
    if isinstance(payload.snapshot, list) and len(payload.snapshot) == 0:
        raise HTTPException(status_code=400, detail="snapshot rows must not be empty")
    try:
        version = versioned_views_service.create_version(
            view_id=view_id,
            snapshot=payload.snapshot,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "View snapshot saved.",
        "data": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/views/{view_id}/versions")
def list_view_versions(view_id: str) -> dict[str, Any]:
    if not view_id.strip():
        raise HTTPException(status_code=400, detail="view_id is required")
    try:
        versions = versioned_views_service.list_versions(view_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "View versions fetched.",
        "data": {
            "versions": versions,
            "count": len(versions),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/views/versions/{version_id}")
def get_view_version(version_id: str) -> dict[str, Any]:
    if not version_id.strip():
        raise HTTPException(status_code=400, detail="version_id is required")
    try:
        version = versioned_views_service.get_version(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if version is None:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    return {
        "success": True,
        "message": "View version fetched.",
        "data": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/views/diff")
def diff_view_versions(payload: DiffVersionsRequest) -> dict[str, Any]:
    if not payload.before_version_id.strip() or not payload.after_version_id.strip():
        raise HTTPException(status_code=400, detail="before_version_id and after_version_id are required")
    if payload.before_version_id.strip() == payload.after_version_id.strip():
        raise HTTPException(status_code=400, detail="before_version_id and after_version_id must differ")
    try:
        diff = versioned_views_service.diff_versions(
            before_version_id=payload.before_version_id,
            after_version_id=payload.after_version_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "success": True,
        "message": "View diff computed.",
        "data": diff,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
