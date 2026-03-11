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
    engineering_validation: "EngineeringValidationReport | None" = None
    control_loops: list["DiscoveredControlLoop"] = Field(default_factory=list)
    completed_logic_model: "CompletedLogicModel | None" = None
    st_validation: "STValidationResult | None" = None
    io_mapping: "IOMappingResult | None" = None
    runtime_validation: "RuntimeValidationResult | None" = None
    simulation_validation: "SimulationValidationResult | None" = None
    version_snapshot: "VersionSnapshotResult | None" = None
    document_confirmation: "DocumentConfirmationResult | None" = None
    confirmation_status: Literal["confirmed", "inferred", "conflict"] | None = None
    generation_report: dict | None = None


class DeployResult(BaseModel):
    project_id: str
    runtime: str
    status: str
    details: str


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"] = "warning"
    related_tags: list[str] = Field(default_factory=list)


class EngineeringValidationReport(BaseModel):
    project_id: str
    status: Literal["passed", "failed"]
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)


class DiscoveredControlLoop(BaseModel):
    loop_tag: str
    sensor_tag: str
    actuator_tag: str
    pv_tag: str | None = None
    sp_tag: str | None = None
    output_tag_analog: str | None = None
    command_tag_bool: str | None = None
    process_unit: str | None = None
    controller_tag: str | None = None
    loop_type: str = "feedback"
    control_strategy: str = "PID"
    setpoint_tag: str | None = None
    output_tag: str | None = None
    sensor_signal_type: Literal["analog", "boolean", "unknown"] = "unknown"
    output_signal_type: Literal["analog", "boolean", "unknown"] = "unknown"
    output_owner: Literal["loop_manager", "equipment_manager", "shared", "unknown"] = "unknown"
    auto_owner: Literal["loop_manager", "equipment_manager", "unknown"] = "unknown"
    manual_owner: Literal["equipment_manager", "loop_manager", "none", "unknown"] = "unknown"
    fail_safe_output_value: str | None = None
    interlock_action_type: Literal["force_output", "disable_loop", "force_command"] | None = None
    interlock_inhibit_tag: str | None = None
    confirmation_status: Literal["CONFIRMED_FROM_DOC", "INFERRED_DEFAULT", "CONTRADICTS_DOCUMENT"] = "INFERRED_DEFAULT"
    confirmation_level: Literal[
        "CONFIRMED_FULL",
        "CONFIRMED_TAGS_ONLY",
        "CONFIRMED_RELATIONSHIP",
        "CONFIRMED_CONTROL_LOOP_CONTEXT",
        "INFERRED_DEFAULT",
        "CONFLICT",
    ] | None = None
    source_reference: str | None = None
    confirmation_note: str | None = None
    mode_tag: str | None = None
    enable_tag: str | None = None
    output_min: float | None = None
    output_max: float | None = None
    confidence: float = 0.7
    status: Literal["inferred", "validated", "needs_review"] = "inferred"


class EquipmentRoutine(BaseModel):
    equipment_tag: str
    routine_name: str
    routine_type: Literal["start_stop", "modulation", "sequence", "interlock"] = "start_stop"
    command_tag: str | None = None
    status_tag: str | None = None
    fault_tag: str | None = None
    equipment_type: str | None = None
    permissive_tags: list[str] = Field(default_factory=list)
    auto_mode_tag: str | None = None
    manual_mode_tag: str | None = None
    run_feedback_tag: str | None = None
    open_command_tag: str | None = None
    close_command_tag: str | None = None
    output_tag: str | None = None
    safe_output_value: str | None = None
    output_owner: Literal["loop_manager", "equipment_manager", "shared", "unknown"] = "unknown"
    auto_owner: Literal["loop_manager", "equipment_manager", "unknown"] = "unknown"
    manual_owner: Literal["equipment_manager", "loop_manager", "none", "unknown"] = "unknown"
    confirmation_status: Literal["CONFIRMED_FROM_DOC", "INFERRED_DEFAULT", "CONTRADICTS_DOCUMENT"] = "INFERRED_DEFAULT"
    confirmation_level: Literal[
        "CONFIRMED_FULL",
        "CONFIRMED_TAGS_ONLY",
        "CONFIRMED_RELATIONSHIP",
        "CONFIRMED_CONTROL_LOOP_CONTEXT",
        "INFERRED_DEFAULT",
        "CONFLICT",
    ] | None = None
    source_reference: str | None = None
    confirmation_note: str | None = None


class AlarmGroup(BaseModel):
    group_name: str
    alarm_tags: list[str] = Field(default_factory=list)
    alarm_rules: list["AlarmRule"] = Field(default_factory=list)
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class AlarmRule(BaseModel):
    source_tag: str
    source_type: str | None = None
    alarm_tag: str
    alarm_type: Literal["HI", "HH", "LO", "LL", "FAULT"]
    comparator: Literal[">", ">=", "<", "<=", "=="]
    threshold_tag: str | None = None
    rationale: str | None = None
    confirmation_status: Literal["CONFIRMED_FROM_DOC", "INFERRED_DEFAULT", "CONTRADICTS_DOCUMENT"] = "INFERRED_DEFAULT"
    confirmation_level: Literal[
        "CONFIRMED_FULL",
        "CONFIRMED_TAGS_ONLY",
        "CONFIRMED_RELATIONSHIP",
        "CONFIRMED_CONTROL_LOOP_CONTEXT",
        "INFERRED_DEFAULT",
        "CONFLICT",
    ] | None = None
    source_reference: str | None = None
    confirmation_note: str | None = None


class InterlockRule(BaseModel):
    interlock_id: str
    source_tag: str
    target_tag: str
    source_type: str | None = None
    comparator: Literal[">", ">=", "<", "<=", "=="] | None = None
    threshold_tag: str | None = None
    target_command_tag: str | None = None
    target_output_tag: str | None = None
    inhibit_tag: str | None = None
    interlock_action_type: Literal["force_output", "disable_loop", "force_command"] | None = None
    safe_value: str | None = None
    action: Literal["trip", "inhibit", "hold", "stop"] = "inhibit"
    rationale: str | None = None
    confirmation_status: Literal["CONFIRMED_FROM_DOC", "INFERRED_DEFAULT", "CONTRADICTS_DOCUMENT"] = "INFERRED_DEFAULT"
    confirmation_level: Literal[
        "CONFIRMED_FULL",
        "CONFIRMED_TAGS_ONLY",
        "CONFIRMED_RELATIONSHIP",
        "CONFIRMED_CONTROL_LOOP_CONTEXT",
        "INFERRED_DEFAULT",
        "CONFLICT",
    ] | None = None
    source_reference: str | None = None
    confirmation_note: str | None = None


class SequenceStep(BaseModel):
    step_number: int
    description: str
    trigger_tag: str | None = None
    transition_tag: str | None = None
    transition_kind: Literal["external", "lifecycle", "immediate"] = "external"
    command_tag: str | None = None
    expected_state: int | None = None
    confirmation_status: Literal["CONFIRMED_FROM_DOC", "INFERRED_DEFAULT", "CONTRADICTS_DOCUMENT"] = "INFERRED_DEFAULT"
    confirmation_level: Literal[
        "CONFIRMED_FULL",
        "CONFIRMED_TAGS_ONLY",
        "CONFIRMED_RELATIONSHIP",
        "CONFIRMED_CONTROL_LOOP_CONTEXT",
        "INFERRED_DEFAULT",
        "CONFLICT",
    ] | None = None
    source_reference: str | None = None
    confirmation_note: str | None = None


class DocumentConfirmationItem(BaseModel):
    element_id: str
    element_type: Literal["equipment", "control_loop", "interlock", "sequence", "alarm"]
    status: Literal["CONFIRMED_FROM_DOC", "INFERRED_DEFAULT", "CONTRADICTS_DOCUMENT"]
    confirmation_level: Literal[
        "CONFIRMED_FULL",
        "CONFIRMED_TAGS_ONLY",
        "CONFIRMED_RELATIONSHIP",
        "CONFIRMED_CONTROL_LOOP_CONTEXT",
        "INFERRED_DEFAULT",
        "CONFLICT",
    ] | None = None
    source_reference: str | None = None
    message: str | None = None
    related_tags: list[str] = Field(default_factory=list)


class DocumentConfirmationResult(BaseModel):
    project_id: str
    equipment_logic: list[DocumentConfirmationItem] = Field(default_factory=list)
    control_loops: list[DocumentConfirmationItem] = Field(default_factory=list)
    interlocks: list[DocumentConfirmationItem] = Field(default_factory=list)
    sequences: list[DocumentConfirmationItem] = Field(default_factory=list)
    alarms: list[DocumentConfirmationItem] = Field(default_factory=list)
    confirmation_status: Literal["confirmed", "inferred", "conflict"] = "inferred"


class CompletedLogicModel(BaseModel):
    project_id: str
    loops: list[DiscoveredControlLoop] = Field(default_factory=list)
    equipment_routines: list[EquipmentRoutine] = Field(default_factory=list)
    alarm_groups: list[AlarmGroup] = Field(default_factory=list)
    interlocks: list[InterlockRule] = Field(default_factory=list)
    startup_sequence: list[SequenceStep] = Field(default_factory=list)
    shutdown_sequence: list[SequenceStep] = Field(default_factory=list)
    fallback_logic_notes: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)


class GeneratedSTFile(BaseModel):
    relative_path: str
    content: str


class STGenerationResult(BaseModel):
    project_id: str
    output_root: str
    files: list[GeneratedSTFile] = Field(default_factory=list)


class STValidationIssue(BaseModel):
    file: str
    rule: str
    message: str
    severity: Literal["warning", "error"] = "error"
    line: int | None = None
    source: str | None = None
    involved_tags: list[str] = Field(default_factory=list)


class STValidationResult(BaseModel):
    project_id: str
    valid: bool
    issues: list[STValidationIssue] = Field(default_factory=list)
    parser_backend: str = "regex"


class IOMappingChannel(BaseModel):
    signal_tag: str
    normalized_signal_tag: str | None = None
    io_type: Literal["AI", "AO", "DI", "DO"]
    plc_slot: int
    plc_channel: int
    source: str = "deterministic"


class IOMappingResult(BaseModel):
    project_id: str
    channels: list[IOMappingChannel] = Field(default_factory=list)


class RuntimeValidationResult(BaseModel):
    project_id: str
    runtime: str
    status: Literal["ready", "not_ready", "todo"]
    checks: list[str] = Field(default_factory=list)
    details: list[str] = Field(default_factory=list)


class SimulationScenarioResult(BaseModel):
    scenario: str
    status: Literal["pass", "fail", "todo"]
    details: str


class SimulationValidationResult(BaseModel):
    project_id: str
    overall_status: Literal["pass", "fail", "todo"]
    scenarios: list[SimulationScenarioResult] = Field(default_factory=list)


class VersionSnapshotResult(BaseModel):
    project_id: str
    snapshot_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifacts: list[str] = Field(default_factory=list)
    backend: str = "filesystem"
