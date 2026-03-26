from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from models.export import (
    DeploymentHandoffRequest,
    DeploymentHandoffResponse,
    ExportReadinessRequest,
    ExportReadinessSummary,
    ExportRequest,
    ExportResponse,
)
from services.export_engine import export_engine

router = APIRouter(tags=["plc-export"])


@router.post("/export", response_model=ExportResponse)
def create_export(payload: ExportRequest) -> ExportResponse:
    result = export_engine.create_export(
        vendor=payload.vendor,
        project_id=payload.project_id,
        source_mode=payload.source_mode,
        source_version_id=payload.source_version_id,
    )
    return ExportResponse.model_validate(result)


@router.post("/export/readiness", response_model=ExportReadinessSummary)
def export_readiness(payload: ExportReadinessRequest) -> ExportReadinessSummary:
    result = export_engine.get_readiness(
        project_id=payload.project_id,
        vendor=payload.vendor,
        source_mode=payload.source_mode,
        source_version_id=payload.source_version_id,
    )
    return ExportReadinessSummary.model_validate(result)


@router.post("/export/deploy-handoff", response_model=DeploymentHandoffResponse)
def export_deploy_handoff(payload: DeploymentHandoffRequest) -> DeploymentHandoffResponse:
    result = export_engine.handoff_deployment(
        project_id=payload.project_id,
        export_id=payload.export_id,
        target_runtime=payload.target_runtime,
        runtime_config=payload.runtime_config,
        trigger_runtime_deploy=payload.trigger_runtime_deploy,
    )
    return DeploymentHandoffResponse.model_validate(result)


@router.get("/exports/{export_id}/download")
def download_export(export_id: str) -> FileResponse:
    package_path, download_name = export_engine.download_export(export_id)
    return FileResponse(path=package_path, filename=download_name, media_type="application/zip")
