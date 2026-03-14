from __future__ import annotations

from fastapi import APIRouter

from models.io_mapping import IOMappingGenerateRequest, IOMappingGenerateResponse
from services.logic_service import logic_service

router = APIRouter(tags=["io-mapping"])


@router.post("/generate-io-mapping", response_model=IOMappingGenerateResponse)
def generate_io_mapping(payload: IOMappingGenerateRequest) -> IOMappingGenerateResponse:
    return IOMappingGenerateResponse.model_validate(logic_service.generate_io_mapping_report(payload.project_id))
