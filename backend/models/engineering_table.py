from pydantic import BaseModel, Field


class EngineeringTableRequest(BaseModel):
    project_id: str
    file_ids: list[str] = Field(default_factory=list)
    include_inferred: bool = True
    max_flow_depth: int = 4


class EngineeringTraceabilityItem(BaseModel):
    source_type: str
    source_id: str
    excerpt: str | None = None
    confidence: float | None = None


class EngineeringTableWarning(BaseModel):
    code: str
    severity: str
    message: str
    affected_tags: list[str] = Field(default_factory=list)


class EngineeringTableSummaryStats(BaseModel):
    total_rows: int
    grounded_rows: int
    inferred_rows: int
    orphan_rows: int
    controlled_rows: int
    actuated_rows: int
    avg_confidence: float
    distinct_systems: int
    distinct_document_sources: int


class EngineeringTableRow(BaseModel):
    id: str
    tag: str
    type: str
    subtype: str | None = None
    description: str | None = None
    system: str | None = None
    equipment: str | None = None
    process_role: str | None = None
    measures: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    controlled_by: list[str] = Field(default_factory=list)
    signal_inputs: list[str] = Field(default_factory=list)
    signal_outputs: list[str] = Field(default_factory=list)
    upstream: list[str] = Field(default_factory=list)
    downstream: list[str] = Field(default_factory=list)
    flow_path: list[str] = Field(default_factory=list)
    current_value: str | None = None
    state: str | None = None
    setpoint: str | None = None
    mode: str | None = None
    unit: str | None = None
    range_min: float | None = None
    range_max: float | None = None
    fail_state: str | None = None
    power: str | None = None
    document_source: list[str] = Field(default_factory=list)
    line_reference: list[str] = Field(default_factory=list)
    confidence: float
    num_connections: int
    num_upstream: int
    num_downstream: int
    control_chain: list[str] = Field(default_factory=list)
    flow_chain: list[str] = Field(default_factory=list)
    is_orphan: bool
    is_controlled: bool
    is_actuated: bool
    warnings: list[str] = Field(default_factory=list)
    grounded_fields: dict[str, object] = Field(default_factory=dict)
    derived_fields: dict[str, object] = Field(default_factory=dict)
    traceability: list[EngineeringTraceabilityItem] = Field(default_factory=list)


class EngineeringTableResponse(BaseModel):
    project_id: str
    rows: list[EngineeringTableRow] = Field(default_factory=list)
    warnings: list[EngineeringTableWarning] = Field(default_factory=list)
    summary: EngineeringTableSummaryStats
