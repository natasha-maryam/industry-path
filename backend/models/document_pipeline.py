from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from models.engineering_table import EngineeringTableRow
from models.pipeline import EngineeringEntity, InferredRelationship, ProcessUnit, RawDocumentChunk, SyntheticNode


DocumentBlockType = Literal["narrative_section", "table", "pid_zone"]
SectionKind = Literal["narrative", "table", "pid_zone"]
IntentType = Literal["flow_control", "level_control", "pressure_control", "temperature_control"]
SupportType = Literal["document_text", "graph_topology", "tag_naming_pattern"]


class SegmentedDocumentBlock(BaseModel):
    section_id: str
    block_id: str
    file_id: str
    file_name: str
    document_id: str
    document_type: str
    kind: SectionKind
    page: int
    page_number: int
    block_type: DocumentBlockType
    text: str
    bbox: tuple[float, float, float, float] | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    section: str | None = None
    zone_name: str | None = None
    table_rows: list[list[str]] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    ocr_used: bool = False


class SegmentedDocument(BaseModel):
    document_id: str
    file_name: str
    document_type: str
    sections: list[SegmentedDocumentBlock] = Field(default_factory=list)


class ExtractedTagRecord(BaseModel):
    normalized_tag: str
    raw_tag: str
    family: str
    canonical_type: str
    normalized_equipment: str = "generic_equipment"
    normalized_type: str = "generic_equipment"
    matched_pattern: str = "fallback:generic_equipment"
    source_section_id: str
    source_section_reference: str
    source_block_id: str
    source_file_id: str
    source_file_name: str
    source_page: int
    source_text: str
    confidence: float = 0.8
    confidence_metadata: dict[str, object] = Field(default_factory=dict)


class NormalizedEquipmentRecord(BaseModel):
    normalized_tag: str
    canonical_type: str
    normalized_name: str
    matched_pattern: str = "fallback:generic_equipment"
    source_section_id: str
    source_section_reference: str
    source_block_id: str
    source_file_id: str
    source_file_name: str
    source_page: int
    source_text: str
    confidence: float = 0.8
    confidence_metadata: dict[str, object] = Field(default_factory=dict)


class ExtractedRelationshipRecord(BaseModel):
    relationship_type: str
    source_tag: str
    target_tag: str
    source_section_id: str
    source_section_reference: str
    source_block_id: str
    source_file_id: str
    source_file_name: str
    source_page: int
    source_text: str
    raw_verb: str | None = None
    confidence: float = 0.7
    confidence_metadata: dict[str, object] = Field(default_factory=dict)


class ExtractedControlIntentRecord(BaseModel):
    intent_type: IntentType
    normalized_verb: str
    source_tag: str | None = None
    target_tag: str | None = None
    related_tags: list[str] = Field(default_factory=list)
    source_section_id: str
    source_section_reference: str
    source_block_id: str
    source_file_id: str
    source_file_name: str
    source_page: int
    source_text: str
    confidence: float = 0.72
    confidence_metadata: dict[str, object] = Field(default_factory=dict)


class EquipmentNormalizationResult(BaseModel):
    normalized_equipment: str
    normalized_type: str
    matched_pattern: str
    confidence: float


GraphRelationshipType = Literal["flow", "control", "measurement"]


class ParserGraphNode(BaseModel):
    tag: str
    canonical_type: str
    display_name: str
    normalized_equipment: str | None = None
    normalized_type: str | None = None
    confidence: float = 0.8
    evidence_references: list[str] = Field(default_factory=list)


class ParserGraphEvidence(BaseModel):
    reference: str
    source_page: int | None = None
    source_text: str | None = None
    method: str | None = None
    raw_verb: str | None = None
    confidence: float | None = None


class ParserGraphEdgeConfidence(BaseModel):
    direct_textual_evidence: float = 0.0
    verb_match_strength: float = 0.0
    tag_pattern_compatibility: float = 0.0
    topology_consistency: float = 0.0


class ParserGraphEdge(BaseModel):
    edge_id: str
    source: str
    target: str
    relationship_type: GraphRelationshipType
    raw_relationship_types: list[str] = Field(default_factory=list)
    confidence_score: float = 0.75
    confidence_factors: ParserGraphEdgeConfidence = Field(default_factory=ParserGraphEdgeConfidence)
    evidence_references: list[str] = Field(default_factory=list)
    evidence: list[ParserGraphEvidence] = Field(default_factory=list)
    related_intent_types: list[IntentType] = Field(default_factory=list)
    raw_verbs: list[str] = Field(default_factory=list)


class ParserGraphContradiction(BaseModel):
    contradiction_type: str
    source: str
    target: str
    relationship_type: GraphRelationshipType
    edge_ids: list[str] = Field(default_factory=list)
    message: str


class ParserRelationshipGraph(BaseModel):
    nodes: list[ParserGraphNode] = Field(default_factory=list)
    edges: list[ParserGraphEdge] = Field(default_factory=list)
    outgoing_adjacency: dict[str, list[str]] = Field(default_factory=dict)
    incoming_adjacency: dict[str, list[str]] = Field(default_factory=dict)
    downstream_map: dict[str, list[str]] = Field(default_factory=dict)
    upstream_map: dict[str, list[str]] = Field(default_factory=dict)
    contradictions: list[ParserGraphContradiction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IntermediateNodeCandidate(BaseModel):
    candidate_id: str
    normalized_tag: str
    canonical_type: str
    display_name: str
    normalized_equipment: str | None = None
    normalized_type: str | None = None
    source_section_ids: list[str] = Field(default_factory=list)
    source_section_references: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)
    source_texts: list[str] = Field(default_factory=list)
    confidence: float = 0.8
    confidence_metadata: dict[str, object] = Field(default_factory=dict)


class IntermediateEdgeCandidate(BaseModel):
    candidate_id: str
    relationship_type: str
    source_tag: str
    target_tag: str
    raw_relationship_types: list[str] = Field(default_factory=list)
    source_section_ids: list[str] = Field(default_factory=list)
    source_section_references: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)
    source_texts: list[str] = Field(default_factory=list)
    related_intent_types: list[IntentType] = Field(default_factory=list)
    raw_verbs: list[str] = Field(default_factory=list)
    confidence: float = 0.75
    confidence_metadata: dict[str, object] = Field(default_factory=dict)


class ExtractionMergeResult(BaseModel):
    node_candidates: list[IntermediateNodeCandidate] = Field(default_factory=list)
    edge_candidates: list[IntermediateEdgeCandidate] = Field(default_factory=list)
    graph: ParserRelationshipGraph = Field(default_factory=ParserRelationshipGraph)


class NormalizedIntentRecord(BaseModel):
    intent_id: str
    intent_type: IntentType
    normalized_verb: str
    source_tag: str | None = None
    target_tag: str | None = None
    related_tags: list[str] = Field(default_factory=list)
    source_text: str
    source_section_id: str
    source_section_reference: str
    source_block_id: str
    source_file_id: str
    source_file_name: str
    source_page: int
    support: list[SupportType] = Field(default_factory=list)
    support_count: int = 0
    confidence: float = 0.75


class ValidationSignalRecord(BaseModel):
    supported: bool = False
    evidence: list[str] = Field(default_factory=list)


class RelationshipValidationDebugRecord(BaseModel):
    candidate_id: str
    source_tag: str
    target_tag: str
    relationship_type: str
    text_support: ValidationSignalRecord = Field(default_factory=ValidationSignalRecord)
    topology_support: ValidationSignalRecord = Field(default_factory=ValidationSignalRecord)
    naming_support: ValidationSignalRecord = Field(default_factory=ValidationSignalRecord)
    support_count: int = 0
    validated: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)


class LoopValidationDebugRecord(BaseModel):
    candidate_id: str
    sensor_tag: str
    actuator_tag: str
    process_node: str
    intent_type: IntentType | None = None
    text_support: ValidationSignalRecord = Field(default_factory=ValidationSignalRecord)
    topology_support: ValidationSignalRecord = Field(default_factory=ValidationSignalRecord)
    naming_support: ValidationSignalRecord = Field(default_factory=ValidationSignalRecord)
    support_count: int = 0
    validated: bool = False
    visible_by_default: bool = True
    visibility_threshold: float = 0.0
    rejection_reasons: list[str] = Field(default_factory=list)


class BehavioralChainRecord(BaseModel):
    chain_id: str
    sensor: str
    actuator: str
    process: str
    chain: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    intent_type: IntentType | None = None
    source_texts: list[str] = Field(default_factory=list)
    support: list[SupportType] = Field(default_factory=list)
    support_count: int = 0
    confidence: float = 0.8


class ValidatedGraphRecord(BaseModel):
    entities: list[EngineeringEntity] = Field(default_factory=list)
    relationships: list[InferredRelationship] = Field(default_factory=list)
    rejected_relationships: list[InferredRelationship] = Field(default_factory=list)
    parser_graph: ParserRelationshipGraph = Field(default_factory=ParserRelationshipGraph)
    warnings: list[str] = Field(default_factory=list)


class PipelineControlLoopRecord(BaseModel):
    loop_id: str
    name: str
    sensor_tag: str
    actuator_tag: str
    process_node: str
    controller_tag: str | None = None
    chain: list[str] = Field(default_factory=list)
    intent_type: IntentType | None = None
    source_texts: list[str] = Field(default_factory=list)
    support: list[SupportType] = Field(default_factory=list)
    support_count: int = 0
    completeness_score: float = 0.0
    continuity_score: float = 0.0
    validation_score: float = 0.0
    relationship_score: float = 0.0
    tuning: dict[str, object] = Field(default_factory=dict)
    confidence: float = 0.8
    tuning_confidence: float = 0.0


class TuningDataRecord(BaseModel):
    tuning_id: str
    loop_reference: str | None = None
    controller_tag: str | None = None
    related_tags: list[str] = Field(default_factory=list)
    kp: float | None = None
    ki: float | None = None
    kd: float | None = None
    reset_time: float | None = None
    ti: float | None = None
    td: float | None = None
    proportional_band: float | None = None
    mode: str | None = None
    behavior_terms: list[str] = Field(default_factory=list)
    setpoint: float | None = None
    output_min: float | None = None
    output_max: float | None = None
    source_section_reference: str | None = None
    source_file_id: str | None = None
    source_file_name: str | None = None
    source_references: list[str] = Field(default_factory=list)
    source_block_id: str
    source_page: int
    source_text: str
    confidence: float = 0.78


class StructuredExtractionLayerResult(BaseModel):
    pid_chunks: list[RawDocumentChunk] = Field(default_factory=list)
    narrative_chunks: list[RawDocumentChunk] = Field(default_factory=list)
    segmented_documents: list[SegmentedDocument] = Field(default_factory=list)
    blocks: list[SegmentedDocumentBlock] = Field(default_factory=list)
    extracted_tags: list[ExtractedTagRecord] = Field(default_factory=list)
    extracted_equipment: list[NormalizedEquipmentRecord] = Field(default_factory=list)
    equipment_detections: list[NormalizedEquipmentRecord] = Field(default_factory=list)
    extracted_relationships: list[ExtractedRelationshipRecord] = Field(default_factory=list)
    extracted_control_intents: list[ExtractedControlIntentRecord] = Field(default_factory=list)
    merge_result: ExtractionMergeResult = Field(default_factory=ExtractionMergeResult)
    warnings: list[str] = Field(default_factory=list)


class SemanticBehaviorLayerResult(BaseModel):
    entities: list[EngineeringEntity] = Field(default_factory=list)
    process_units: list[ProcessUnit] = Field(default_factory=list)
    synthetic_nodes: list[SyntheticNode] = Field(default_factory=list)
    semantic_intents: list[NormalizedIntentRecord] = Field(default_factory=list)
    normalized_intents: list[NormalizedIntentRecord] = Field(default_factory=list)
    behavioral_chains: list[BehavioralChainRecord] = Field(default_factory=list)
    supported_relationships: list[InferredRelationship] = Field(default_factory=list)
    rejected_relationships: list[InferredRelationship] = Field(default_factory=list)
    relationship_validation_debug: list[RelationshipValidationDebugRecord] = Field(default_factory=list)
    metadata_by_entity: dict[str, dict[str, object]] = Field(default_factory=dict)
    rule_bundle: dict[str, list[object]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ValidationControlLoopLayerResult(BaseModel):
    validated_graph: ValidatedGraphRecord
    nodes: list[dict[str, object]] = Field(default_factory=list)
    edges: list[dict[str, object]] = Field(default_factory=list)
    control_loops: list[PipelineControlLoopRecord] = Field(default_factory=list)
    rejected_control_loops: list[PipelineControlLoopRecord] = Field(default_factory=list)
    loop_validation_debug: list[LoopValidationDebugRecord] = Field(default_factory=list)
    tuning_data: list[TuningDataRecord] = Field(default_factory=list)
    low_confidence_relationships: list[InferredRelationship] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FinalValidationDiagnostics(BaseModel):
    total_tags: int = 0
    rejected_tags: int = 0
    total_relationships: int = 0
    rejected_relationships: int = 0
    total_loops: int = 0
    rejected_loops: int = 0
    inferred_links: int = 0
    duplicate_edges_removed: int = 0
    duplicate_loops_removed: int = 0


class FinalValidationLayerResult(BaseModel):
    validated_graph: ValidatedGraphRecord
    tag_rows: list[EngineeringTableRow] = Field(default_factory=list)
    rejected_tag_rows: list[EngineeringTableRow] = Field(default_factory=list)
    control_loops: list[PipelineControlLoopRecord] = Field(default_factory=list)
    rejected_control_loops: list[PipelineControlLoopRecord] = Field(default_factory=list)
    tuning_data: list[TuningDataRecord] = Field(default_factory=list)
    diagnostics: FinalValidationDiagnostics = Field(default_factory=FinalValidationDiagnostics)
    warnings: list[str] = Field(default_factory=list)


class DocumentParsingPipelineResult(BaseModel):
    structured_extraction: StructuredExtractionLayerResult
    semantic_behavior: SemanticBehaviorLayerResult
    validation_control_loop: ValidationControlLoopLayerResult
    final_validation: FinalValidationLayerResult
    warnings: list[str] = Field(default_factory=list)
