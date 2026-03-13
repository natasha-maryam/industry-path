from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    status: str = "healthy"
    description: str | None = None
    source_documents: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    alarms: list[str] = Field(default_factory=list)
    interlocks: list[str] = Field(default_factory=list)
    mode: str | None = None
    linked_logic: list[str] = Field(default_factory=list)
    process_unit: str | None = None
    cluster_id: str | None = None
    cluster_name: str | None = None
    cluster_order: int | None = None
    node_rank: int | None = None
    preferred_direction: str | None = None
    confidence: float = 0.8
    is_synthetic: bool = False
    explanation: str | None = None
    source_references: list[str] = Field(default_factory=list)
    equipment_type: str | None = None
    signal_type: str | None = None
    instrument_role: str | None = None
    control_role: str | None = None
    power_rating: str | None = None
    connected_to: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    control_path: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    metadata_confidence: dict[str, float] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str
    edge_class: str = "process"
    line_style: str = "solid"
    confidence: float = 0.7
    explanation: str | None = None
    inference_source: str | None = None
    source_references: list[str] = Field(default_factory=list)
    edge_label: str | None = None
    semantic_kind: str | None = None
    process_flow_direction: str | None = None


class PlantGraph(BaseModel):
    project_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class TraceResponse(BaseModel):
    project_id: str
    node_id: str
    path: list[str]
