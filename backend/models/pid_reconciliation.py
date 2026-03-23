from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PIDInstrumentationRecord(BaseModel):
    tag: str
    label: str | None = None
    node_type: str | None = None
    status: str | None = "healthy"
    process_unit: str | None = None
    connected_to: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)


class PIDReconcileRequest(BaseModel):
    dataset: list[PIDInstrumentationRecord] = Field(default_factory=list)
    similarity_threshold: float = Field(default=0.9, ge=0.5, le=1.0)


class PIDApplyUpdateRequest(BaseModel):
    allow_conflicts: bool = False
    force_apply_on_validation_warnings: bool = False


class PIDChangeEntry(BaseModel):
    tag: str
    details: str


class PIDTopologyChange(BaseModel):
    edge_id: str
    source: str
    target: str
    edge_type: str
    change: Literal["added", "removed"]


class PIDConflict(BaseModel):
    incoming_tag: str
    existing_tag: str
    similarity: float
    reason: str


class PIDReconcileSummary(BaseModel):
    project_id: str
    generated_at: datetime
    similarity_threshold: float
    new_devices: list[PIDChangeEntry] = Field(default_factory=list)
    deprecated_devices: list[PIDChangeEntry] = Field(default_factory=list)
    topology_changes: list[PIDTopologyChange] = Field(default_factory=list)
    possible_conflicts: list[PIDConflict] = Field(default_factory=list)
    apply_ready: bool = False


class PIDApplyUpdateResponse(BaseModel):
    project_id: str
    applied_at: datetime
    nodes_count: int
    edges_count: int
    validation_status: str
    commit_triggered: bool
    summary: str
