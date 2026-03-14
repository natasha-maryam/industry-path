from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.st_verifier import STVerifyRequest, STVerifyResponse
from services.st_validator import verify_st_workspace

router = APIRouter(tags=["st-verifier"])


@router.post("/verify-st", response_model=STVerifyResponse)
def verify_st(payload: STVerifyRequest) -> STVerifyResponse:
    try:
        return STVerifyResponse.model_validate(verify_st_workspace(payload.workspace_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"ST workspace verification failed: {exc}") from exc
