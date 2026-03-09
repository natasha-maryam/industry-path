from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DocumentType = Literal["pid_pdf", "control_narrative", "unknown_document"]
CanonicalType = Literal[
    "pump",
    "valve",
    "control_valve",
    "flow_transmitter",
    "level_transmitter",
    "level_switch",
    "pressure_transmitter",
    "differential_pressure_transmitter",
    "analyzer",
    "blower",
    "tank",
    "basin",
    "clarifier",
    "chemical_system_device",
    "generic_device",
    "process_unit",
]
RelationshipType = Literal[
    "PROCESS_FLOW",
    "CONNECTED_TO",
    "FEEDS",
    "DISCHARGES_TO",
    "SUPPLIES_AIR_TO",
    "MEASURES",
    "CONTROLS",
    "SIGNAL_TO",
    "PART_OF",
    "MONITORS",
    "INTERLOCKS_WITH",
    "ALARMS_ON",
    "SUPPORTS",
    "LOCATED_IN",
    "ASSOCIATED_WITH",
]
ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW"]


class RawDocumentChunk(BaseModel):
    file_id: str
    file_name: str
    document_type: DocumentType
    page_number: int
    text: str
    section: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    ocr_used: bool = False


class DetectedTag(BaseModel):
    normalized_tag: str
    raw_tag: str
    family: str
    canonical_type: CanonicalType
    source_file_id: str
    source_file_name: str
    source_page: int
    source_text: str
    confidence: float = 0.8


class EngineeringEntity(BaseModel):
    id: str
    tag: str
    canonical_type: CanonicalType
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    process_unit: str | None = None
    source_documents: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)
    source_snippets: list[str] = Field(default_factory=list)
    confidence: float = 0.8
    cluster_id: str | None = None
    cluster_name: str | None = None
    cluster_order: int | None = None
    node_rank: int | None = None
    preferred_direction: str | None = None
    is_synthetic: bool = False
    explanation: str | None = None
    source_references: list[str] = Field(default_factory=list)
    parse_notes: list[str] = Field(default_factory=list)


class ProcessUnit(BaseModel):
    id: str
    name: str
    canonical_type: Literal[
        "pump_station",
        "screening_unit",
        "grit_unit",
        "aeration_basin",
        "clarifier",
        "sludge_handling",
        "chemical_feed",
        "blower_package",
        "air_header",
        "tank",
        "generic_process_unit",
    ]
    aliases: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    confidence: float = 0.75


class SyntheticNode(BaseModel):
    id: str
    label: str
    canonical_type: CanonicalType = "process_unit"
    process_unit: str | None = None
    confidence: float = 0.7
    explanation: str
    source_references: list[str] = Field(default_factory=list)


class ControlLoopDefinition(BaseModel):
    name: str
    source_sentence: str
    page_number: int
    related_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.8


class AlarmDefinition(BaseModel):
    name: str
    source_sentence: str
    page_number: int
    related_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.8


class InterlockDefinition(BaseModel):
    name: str
    source_sentence: str
    page_number: int
    related_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.8


class SequenceDefinition(BaseModel):
    sequence_type: Literal["startup", "shutdown"]
    source_sentence: str
    page_number: int
    related_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.75


class ModeDefinition(BaseModel):
    mode_name: str
    source_sentence: str
    page_number: int
    related_tags: list[str] = Field(default_factory=list)
    confidence: float = 0.7


class InferredRelationship(BaseModel):
    relationship_type: RelationshipType
    source_entity: str
    target_entity: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    inference_source: Literal["narrative", "heuristic", "locality", "merged", "assignment", "refinement", "validation"]
    explanation: str
    source_references: list[str] = Field(default_factory=list)


class GraphWarning(BaseModel):
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    related_entities: list[str] = Field(default_factory=list)


class ClusterAssignment(BaseModel):
    entity_id: str
    process_unit: str
    cluster_id: str
    cluster_name: str
    cluster_order: int = 99
    node_rank: int = 0
    preferred_direction: Literal["LR", "TB"] = "LR"


class ParseBatchResult(BaseModel):
    entities: list[EngineeringEntity] = Field(default_factory=list)
    relationships: list[InferredRelationship] = Field(default_factory=list)
    control_loops: list[ControlLoopDefinition] = Field(default_factory=list)
    alarms: list[AlarmDefinition] = Field(default_factory=list)
    interlocks: list[InterlockDefinition] = Field(default_factory=list)
    sequences: list[SequenceDefinition] = Field(default_factory=list)
    modes: list[ModeDefinition] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
