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


class PlantGraph(BaseModel):
    project_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class TraceResponse(BaseModel):
    project_id: str
    node_id: str
    path: list[str]
