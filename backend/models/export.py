from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ExportVendor = Literal["siemens", "rockwell", "codesys", "beckhoff", "openplc", "generic_st"]
ExportSourceMode = Literal["live", "version"]
ReadinessLevel = Literal["success", "warning", "error"]
DeploymentReadinessState = Literal["not_ready", "ready_to_deploy", "deployment_in_progress", "deployed", "failed"]


class ExportReadinessItem(BaseModel):
    key: str
    label: str
    ready: bool
    level: ReadinessLevel
    message: str


class ExportReadinessSummary(BaseModel):
    project_id: str
    vendor: ExportVendor
    source_mode: ExportSourceMode = "live"
    source_version_id: str | None = None
    checks: list[ExportReadinessItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    export_allowed: bool = False
    export_blocked: bool = True
    deploy_allowed: bool = False
    deploy_blocked: bool = True
    unresolved_physical_io_tags: list[str] = Field(default_factory=list)
    unresolved_internal_tags: list[str] = Field(default_factory=list)
    auto_resolved_derived_tags: list[str] = Field(default_factory=list)
    unknown_unclassified_tags: list[str] = Field(default_factory=list)
    export_blockers: list[str] = Field(default_factory=list)
    deploy_blockers: list[str] = Field(default_factory=list)
    generated_at: datetime


class ExportRequest(BaseModel):
    project_id: str
    vendor: ExportVendor
    source_mode: ExportSourceMode = "live"
    source_version_id: str | None = None


class ExportResponse(BaseModel):
    export_id: str
    project_id: str
    project_name: str
    vendor: ExportVendor
    source_mode: ExportSourceMode = "live"
    source_version_id: str | None = None
    generated_at: datetime
    files: list[str] = Field(default_factory=list)
    download_url: str
    package_path: str | None = None
    artifact_name: str | None = None
    logic_block_count: int = 0
    tag_count: int = 0
    readiness: ExportReadinessSummary | None = None
    package_preview: list[str] = Field(default_factory=list)


class ExportReadinessRequest(BaseModel):
    project_id: str
    vendor: ExportVendor = "siemens"
    source_mode: ExportSourceMode = "live"
    source_version_id: str | None = None


class DeploymentHandoffRequest(BaseModel):
    project_id: str
    export_id: str
    target_runtime: str
    runtime_config: dict[str, object] = Field(default_factory=dict)
    trigger_runtime_deploy: bool = False


class DeploymentHandoffResponse(BaseModel):
    project_id: str
    export_id: str
    target_runtime: str
    state: DeploymentReadinessState
    message: str
    logs: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    package_path: str | None = None
