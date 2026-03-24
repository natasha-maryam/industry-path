from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from models.versioning import (
    VersionActionResponse,
    VersionCommitRequest,
    VersionDiffResponse,
    VersionHistoryResponse,
    VersionRollbackRequest,
    VersionSnapshotRequest,
)
from services.version_manager import version_manager

router = APIRouter(prefix="/versions", tags=["versions"])


@router.post("/commit", response_model=VersionActionResponse)
def commit_version(payload: VersionCommitRequest) -> VersionActionResponse:
    try:
        result = version_manager.auto_commit(
            project_id=payload.project_id,
            trigger_source=payload.trigger_source,
            summary=payload.summary,
        )
        return VersionActionResponse.model_validate(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/snapshot", response_model=VersionActionResponse)
def create_version_snapshot(payload: VersionSnapshotRequest) -> VersionActionResponse:
    try:
        result = version_manager.auto_commit(
            project_id=payload.project_id,
            trigger_source=payload.trigger_source,
            summary=payload.summary,
        )
        return VersionActionResponse.model_validate(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history", response_model=VersionHistoryResponse)
def get_version_history(project_id: str = Query(...)) -> VersionHistoryResponse:
    try:
        records = version_manager.get_history(project_id)
        return VersionHistoryResponse(project_id=project_id, records=records)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{version_id}")
def get_version(version_id: str, project_id: str = Query(...)) -> dict[str, object]:
    try:
        record = version_manager.get_version(project_id, version_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")
        return record
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rollback")
def rollback_version(payload: VersionRollbackRequest) -> dict[str, object]:
    try:
        return version_manager.rollback_to_version(
            project_id=payload.project_id,
            version_tag=payload.version_tag,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/diff/{version_id}", response_model=VersionDiffResponse)
def diff_version(version_id: str, project_id: str = Query(...), compare_to: str | None = Query(default=None)) -> VersionDiffResponse:
    try:
        if compare_to:
            result = version_manager.diff_versions(project_id, compare_to, version_id)
            return VersionDiffResponse.model_validate(result)

        history = version_manager.get_history(project_id)
        ordered = [item.get("version_tag") for item in history if item.get("version_tag")]
        if version_id not in ordered:
            raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")
        idx = ordered.index(version_id)
        if idx == len(ordered) - 1:
            raise HTTPException(status_code=400, detail="No previous version available for diff. Provide compare_to.")

        base = ordered[idx + 1]
        result = version_manager.diff_versions(project_id, base, version_id)
        return VersionDiffResponse.model_validate(result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
