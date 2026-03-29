from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from models.document_pipeline import FinalValidationDiagnostics


DocumentType = Literal["pid_pdf", "control_narrative", "unknown_document"]


class ParseBatchRequest(BaseModel):
    file_ids: list[str] = Field(default_factory=list)


class FinalTagOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    tag: str
    equipment: str
    upstream: list[str] = Field(default_factory=list)
    downstream: list[str] = Field(default_factory=list)


class FinalLoopOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    loop_id: str
    sensor: str
    actuator: str
    process: str
    chain: list[str] = Field(default_factory=list)
    confidence: float
    tuning_confidence: float = 0.0
    controller: str | None = None


class ParseUnifiedModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    tags: list[FinalTagOutput] = Field(default_factory=list)
    tag_rows: list[FinalTagOutput] = Field(default_factory=list)
    control_loops: list[FinalLoopOutput] = Field(default_factory=list)
    rejected_control_loops: list[FinalLoopOutput] = Field(default_factory=list)
    final_validation_diagnostics: FinalValidationDiagnostics = Field(default_factory=FinalValidationDiagnostics)


class ParseBatchResponse(BaseModel):
    project_id: str
    parse_job_id: str
    parse_batch_id: str
    parsed_at: str
    documents_seen: int
    documents: list[str]
    document_types: list[str]
    entities_count: int
    nodes_count: int
    edges_count: int
    final_validation_diagnostics: FinalValidationDiagnostics = Field(default_factory=FinalValidationDiagnostics)
    unified_model: ParseUnifiedModel
    warnings: list[str] = Field(default_factory=list)
    summary: str


class ParseJobStatusResponse(BaseModel):
    parse_job_id: str
    project_id: str
    parse_batch_id: str | None = None
    status: str
    current_stage: str | None = None
    stage_message: str | None = None
    progress_percent: float = 0.0
    nodes_count: int = 0
    edges_count: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class ParseSuggestion(BaseModel):
    relationship_type: str
    source_entity: str
    target_entity: str
    confidence_score: float
    confidence_level: str
    inference_source: str
    explanation: str
    source_references: list[str] = Field(default_factory=list)


class ParseSuggestionsResponse(BaseModel):
    project_id: str
    parse_batch_id: str
    suggestions: list[ParseSuggestion] = Field(default_factory=list)
