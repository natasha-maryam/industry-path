from fastapi import APIRouter, HTTPException

from models.copilot import (
    CopilotAsyncRunResponse,
    CopilotJobStatusResponse,
    CopilotProviderRequest,
    CopilotProviderResponse,
    CopilotRunRequest,
    CopilotRunResponse,
)
from services.copilot_production import copilot_production, get_job, run_job
from services.copilot_scenario_engine import copilot_engine


router = APIRouter(prefix="/copilot", tags=["copilot"])


def _resolve_connector(payload: CopilotRunRequest) -> str:
    connector = str(payload.connector or payload.provider or "").strip()
    if not connector:
        raise ValueError("connector is required")
    return connector


@router.post("/run", response_model=CopilotRunResponse)
def run_copilot(payload: CopilotRunRequest) -> CopilotRunResponse:
    try:
        return copilot_engine.run(payload.command, connector=_resolve_connector(payload), context=payload.context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run_async", response_model=CopilotAsyncRunResponse)
def run_copilot_async(payload: CopilotRunRequest) -> CopilotAsyncRunResponse:
    try:
        job = run_job(copilot_production.run, payload.command, _resolve_connector(payload), payload.context)
        return CopilotAsyncRunResponse(**job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status/{job_id}", response_model=CopilotJobStatusResponse)
def get_copilot_status(job_id: str) -> CopilotJobStatusResponse:
    try:
        job = get_job(job_id)
        return CopilotJobStatusResponse(**job)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc


@router.post("/provider", response_model=CopilotProviderResponse)
def register_provider(payload: CopilotProviderRequest) -> CopilotProviderResponse:
    try:
        result = copilot_engine.register_provider(
            payload.name,
            mock_response=payload.mock_response,
            metadata=payload.metadata,
        )
        copilot_production.register_provider(
            payload.name,
            mock_response=payload.mock_response,
            metadata=payload.metadata,
        )
        return CopilotProviderResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc