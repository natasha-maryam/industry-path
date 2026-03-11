from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DocumentParseResult(BaseModel):
    project_id: str
    files_processed: int
    chunks_extracted: int
    warnings: list[str] = Field(default_factory=list)


class NormalizedTag(BaseModel):
    raw_tag: str
    canonical_tag: str
    canonical_type: str | None = None


class PlantNode(BaseModel):
    id: str
    node_type: str
    process_unit: str | None = None


class PlantEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    confidence: float = 0.7


class PlantModel(BaseModel):
    project_id: str
    nodes: list[PlantNode] = Field(default_factory=list)
    edges: list[PlantEdge] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"] = "warning"
    related_tags: list[str] = Field(default_factory=list)


class ControlLoop(BaseModel):
    loop_tag: str
    sensor_tag: str
    actuator_tag: str
    strategy: str
    confidence: float


class EquipmentRoutine(BaseModel):
    equipment_tag: str
    command_tag: str | None = None
    status_tag: str | None = None
    fault_tag: str | None = None


class AlarmRule(BaseModel):
    alarm_tag: str
    source_tag: str
    comparator: str
    threshold_tag: str | None = None


class InterlockRule(BaseModel):
    interlock_id: str
    source_tag: str
    target_tag: str
    condition: str


class SequenceStep(BaseModel):
    step_number: int
    description: str
    transition_condition: str | None = None


class LogicModel(BaseModel):
    project_id: str
    loops: list[ControlLoop] = Field(default_factory=list)
    equipment: list[EquipmentRoutine] = Field(default_factory=list)
    alarms: list[AlarmRule] = Field(default_factory=list)
    interlocks: list[InterlockRule] = Field(default_factory=list)
    startup_sequence: list[SequenceStep] = Field(default_factory=list)
    shutdown_sequence: list[SequenceStep] = Field(default_factory=list)


class GeneratedLogicFile(BaseModel):
    relative_path: str
    absolute_path: str
    bytes_written: int


class IOMappingEntry(BaseModel):
    signal_tag: str
    io_type: Literal["AI", "AO", "DI", "DO"]
    channel: int


class GenerationReport(BaseModel):
    project_id: str
    generated_files: list[GeneratedLogicFile] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)
    io_mapping: list[IOMappingEntry] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
