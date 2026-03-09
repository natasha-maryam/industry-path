from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class LogicGenerateRequest(BaseModel):
    strategy: str = Field(default="default")


class LogicArtifact(BaseModel):
    project_id: str
    file_name: str = "main.st"
    code: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


RuleType = Literal[
    "start_stop",
    "open_close",
    "modulate",
    "alarm",
    "interlock",
    "lead_lag",
    "mode",
    "setpoint_control",
    "pid_loop",
    "sequence",
    "ratio_control",
]

RuleGroup = Literal[
    "influent_pump_station",
    "screening",
    "grit_removal",
    "aeration",
    "blower_package",
    "chemical_feed",
    "clarifier",
    "startup_shutdown",
    "alarms",
    "modes",
    "general",
]

ConditionKind = Literal[
    "level",
    "pressure",
    "differential_pressure",
    "analyzer",
    "flow",
    "timer",
    "fault",
    "mode",
    "sequence_state",
    "boolean_state",
]

RuleAction = Literal[
    "START",
    "STOP",
    "OPEN",
    "CLOSE",
    "MODULATE",
    "ALARM",
    "SWITCH_TO_LEAD",
    "SWITCH_TO_LAG",
    "ENABLE",
    "DISABLE",
    "HOLD",
    "SHUTDOWN",
]

RuleOperator = Literal[">", "<", ">=", "<=", "==", "state_change", "timer_elapsed", "manual_command"]


class NarrativeSentence(BaseModel):
    id: str
    project_id: str
    page_number: int | None = None
    section_heading: str | None = None
    text: str


class ControlRuleCandidate(BaseModel):
    id: str
    project_id: str
    sentence_id: str
    rule_type: RuleType
    source_sentence: str
    source_page: int | None = None
    section_heading: str | None = None
    rule_group: RuleGroup = "general"
    confidence: float = 0.7
    reasons: list[str] = Field(default_factory=list)


class ControlRule(BaseModel):
    id: str
    project_id: str
    rule_group: RuleGroup = "general"
    rule_type: RuleType
    source_tag: str | None = None
    source_type: str | None = None
    condition_kind: ConditionKind | None = None
    operator: RuleOperator | None = None
    threshold: str | None = None
    threshold_name: str | None = None
    action: RuleAction
    target_tag: str | None = None
    target_type: str | None = None
    secondary_target_tag: str | None = None
    mode: str | None = None
    priority: int = 50
    confidence: float = 0.0
    source_sentence: str
    source_page: int | None = None
    section_heading: str | None = None
    explanation: str | None = None
    resolution_strategy: str = "exact_tag"
    is_symbolic: bool = False
    renderable: bool = True
    unresolved_tokens: list[str] = Field(default_factory=list)
    comments: list[str] = Field(default_factory=list)
    display_text: str
    st_preview: str
    source_references: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RejectedRuleCandidate(BaseModel):
    candidate_id: str
    rule_type: RuleType
    source_sentence: str
    section_heading: str | None = None
    source_page: int | None = None
    reason: str


class LogicGenerationResult(LogicArtifact):
    run_id: str
    project_version: int | None = None
    generator_version: str | None = None
    rules_count: int
    warnings_count: int = 0
    rules: list[ControlRule] = Field(default_factory=list)
    structured_rules: list[ControlRule] = Field(default_factory=list)
    final_rendered_rules: list[ControlRule] = Field(default_factory=list)
    symbolic_rendered_rules: list[ControlRule] = Field(default_factory=list)
    groups: dict[str, list[ControlRule]] = Field(default_factory=dict)
    st_preview: str = ""
    rejected_candidates: list[RejectedRuleCandidate] = Field(default_factory=list)
    rejected_rules: list[RejectedRuleCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DeployResult(BaseModel):
    project_id: str
    runtime: str
    status: str
    details: str
