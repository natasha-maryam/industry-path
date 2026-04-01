from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


CopilotMode = Literal["connector_gateway"]
CopilotAsyncJobStatus = Literal["queued", "running", "completed", "failed"]
CopilotProductionResultType = Literal["connector"]


class CopilotRunRequest(BaseModel):
    command: str = Field(min_length=1)
    connector: str | None = Field(default=None, min_length=1)
    provider: str | None = Field(default=None, min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class CopilotRunResponse(BaseModel):
    success: bool = True
    command: str
    connector: str
    mode: CopilotMode
    request: str | None = None
    warnings: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CopilotProviderRequest(BaseModel):
    name: str = Field(min_length=1)
    mock_response: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CopilotProviderResponse(BaseModel):
    connector: str
    registered: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CopilotProductionResult(BaseModel):
    type: CopilotProductionResultType
    summary: str
    warnings: list[str] = Field(default_factory=list)
    request: str | None = None
    cached: bool = False
    connector: str
    data: dict[str, Any] = Field(default_factory=dict)


class CopilotAsyncRunResponse(BaseModel):
    success: bool = True
    job_id: str
    status: CopilotAsyncJobStatus
    command: str
    connector: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CopilotJobStatusResponse(BaseModel):
    success: bool = True
    job_id: str
    status: CopilotAsyncJobStatus
    command: str | None = None
    connector: str | None = None
    submitted_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    error_code: str | None = None
    result: CopilotProductionResult | None = None