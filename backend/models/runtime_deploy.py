from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RuntimeStepStatus = Literal["passed", "failed"]
RuntimeOverallStatus = Literal["passed", "failed"]


class RuntimeDeployRequest(BaseModel):
    project_id: str
    workspace_path: str = ""
    runtime_config: dict[str, Any] = Field(default_factory=dict)


class RuntimeDeploySummary(BaseModel):
    files_loaded: int = 0
    io_points_bound: int = 0
    runtime_target: str = "OpenPLC"
    project_name: str


class RuntimeDeployStep(BaseModel):
    name: Literal["create_project", "import_st", "apply_io_config", "start_runtime"]
    status: RuntimeStepStatus
    message: str


class RuntimeDeployResponse(BaseModel):
    status: RuntimeOverallStatus
    summary: RuntimeDeploySummary
    steps: list[RuntimeDeployStep] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
