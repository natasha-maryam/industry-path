from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.io_mapping import IOMappingGenerateResponse
from services.logic_service import logic_service

router = APIRouter(prefix="/projects/{project_id}/io-mapping", tags=["io-mapping"])


@router.get("/latest", response_model=IOMappingGenerateResponse)
def get_latest_io_mapping(project_id: str) -> IOMappingGenerateResponse:
    latest = logic_service.get_latest_io_mapping(project_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="No IO mapping has been generated for this project.")
    return IOMappingGenerateResponse.model_validate(latest)


@router.post("/generate", response_model=IOMappingGenerateResponse)
def generate_io_mapping(project_id: str) -> IOMappingGenerateResponse:
    return IOMappingGenerateResponse.model_validate(logic_service.generate_io_mapping_report(project_id))


@router.post("/versions/{version_id}/activate", response_model=IOMappingGenerateResponse)
def activate_io_mapping_version(project_id: str, version_id: str) -> IOMappingGenerateResponse:
    activated = logic_service.set_active_io_mapping_version(project_id, version_id)
    if activated is None:
        raise HTTPException(status_code=404, detail=f"IO mapping version not found: {version_id}")
    return IOMappingGenerateResponse.model_validate(activated)
