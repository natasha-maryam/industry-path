from typing import Literal

from pydantic import BaseModel, Field


DocumentType = Literal["pid_pdf", "control_narrative", "unknown_document"]


class ParseBatchRequest(BaseModel):
    file_ids: list[str] = Field(default_factory=list)


class ParseBatchResponse(BaseModel):
    project_id: str
    parse_job_id: str
    parse_batch_id: str
    parsed_at: str
    documents_seen: int
    documents: list[str]
    document_types: list[str]
    nodes_count: int
    edges_count: int
    unified_model: dict[str, object]
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
