from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RuntimeDeploymentRecord(BaseModel):
    id: str
    project_id: str
    target_runtime: str
    protocol: str
    plc_address: str | None = None
    io_config_json: list[dict] = Field(default_factory=list)
    deploy_status: str
    validation_status: str
    deployed_version: str | None = None
    artifact_path: str | None = None
    last_error: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RuntimeStateResponse(BaseModel):
    project_id: str
    runtime_state: str
    deployment: RuntimeDeploymentRecord | None = None
    live_runtime: dict = Field(default_factory=dict)
