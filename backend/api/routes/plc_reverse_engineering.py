from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.plc_reverse_engineering import PLCPhase1ExtractionResponse
from services.plc_reverse_engineering_service import plc_reverse_engineering_service

router = APIRouter(prefix="/plc/reverse-engineering", tags=["plc-reverse-engineering"])


@router.post("/phase1", response_model=PLCPhase1ExtractionResponse)
async def run_phase1_reverse_engineering(
    files: list[UploadFile] = File(...),
    document_types: list[str] | None = Form(default=None),
    project_id: str | None = Form(default=None),
) -> PLCPhase1ExtractionResponse:
    try:
        return await plc_reverse_engineering_service.run_phase1(
            files=files,
            document_types=document_types,
            project_id=project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
