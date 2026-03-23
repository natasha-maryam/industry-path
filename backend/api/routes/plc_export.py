from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from models.export import ExportRequest, ExportResponse
from services.export_engine import export_engine

router = APIRouter(tags=["plc-export"])


@router.post("/export", response_model=ExportResponse)
def create_export(payload: ExportRequest) -> ExportResponse:
    result = export_engine.create_export(vendor=payload.vendor, project_id=payload.project_id)
    return ExportResponse.model_validate(result)


@router.get("/exports/{export_id}/download")
def download_export(export_id: str) -> FileResponse:
    package_path, download_name = export_engine.download_export(export_id)
    return FileResponse(path=package_path, filename=download_name, media_type="application/zip")
