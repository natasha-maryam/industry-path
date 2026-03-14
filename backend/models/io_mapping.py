from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


IOMappingStatus = Literal["passed", "passed_with_warnings", "failed"]
IOMappingIssueSeverity = Literal["warning", "error"]


class IOMappingGenerateRequest(BaseModel):
    project_id: str


class IOMappingSummary(BaseModel):
    total_signals: int = 0
    warning_count: int = 0
    error_count: int = 0


class IOMappingRow(BaseModel):
    tag: str
    device_type: str
    signal_type: str
    io_type: str
    plc_id: str
    slot: int
    channel: int
    description: str = ""


class IOMappingIssue(BaseModel):
    code: str
    severity: IOMappingIssueSeverity
    message: str
    tag: str | None = None


class IOMappingGenerateResponse(BaseModel):
    project_id: str = ""
    version_id: str | None = None
    version_number: int | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    status: IOMappingStatus
    summary: IOMappingSummary
    rows: list[IOMappingRow] = Field(default_factory=list)
    issues: list[IOMappingIssue] = Field(default_factory=list)
