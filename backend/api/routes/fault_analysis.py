from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.root_cause_engine import root_cause_engine

router = APIRouter(tags=["fault-analysis"])


class AnalyzeFaultRequest(BaseModel):
    alarm_tag: str | None = None
    selected_tag: str | None = None
    project_id: str | None = None


@router.post("/analyze_fault")
def analyze_fault(payload: AnalyzeFaultRequest) -> dict[str, Any]:
    alarm_tag = (payload.selected_tag or payload.alarm_tag or "").strip()
    if not alarm_tag:
        raise HTTPException(status_code=400, detail="selected_tag or alarm_tag is required")
    return root_cause_engine.analyze_alarm(alarm_tag=alarm_tag, project_id=payload.project_id)
