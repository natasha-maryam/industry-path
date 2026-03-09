from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from models.logic import ControlRuleCandidate


@dataclass
class ExtractedRuleDraft:
    rule_group: str
    rule_type: str
    source_tag: str | None
    source_type: str | None
    condition_kind: str | None
    operator: str | None
    threshold: str | None
    threshold_name: str | None
    action: str
    target_tag: str | None
    target_type: str | None
    secondary_target_tag: str | None
    mode: str | None
    priority: int
    confidence: float
    source_sentence: str
    source_page: int | None
    section_heading: str | None
    explanation: str
    resolution_strategy: str = "alias_match"
    renderable: bool = True
    unresolved_tokens: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    source_references: list[str] = field(default_factory=list)


class ControlRuleExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.tag_pattern = re.compile(r"\b[A-Z]{2,6}[-_ ]?\d{2,5}[A-Z]?\b")
        self.operator_patterns: list[tuple[re.Pattern[str], str]] = [
            (re.compile(r"\bgreater than or equal to\b|\bat least\b", re.IGNORECASE), ">="),
            (re.compile(r"\bless than or equal to\b|\bat most\b", re.IGNORECASE), "<="),
            (re.compile(r"\bgreater than\b|\babove\b|\bhigh\b", re.IGNORECASE), ">"),
            (re.compile(r"\bless than\b|\bbelow\b|\blow\b", re.IGNORECASE), "<"),
            (re.compile(r"\bequals\b", re.IGNORECASE), "=="),
        ]

    @staticmethod
    def _normalize_token(token: str) -> str:
        return token.upper().replace("_", "-").replace(" ", "-")

    @staticmethod
    def _canonical_token(token: str) -> str:
        return token.upper().replace("-", "_")

    def _infer_operator(self, sentence: str) -> str | None:
        for pattern, op in self.operator_patterns:
            if pattern.search(sentence):
                return op
        return None

    def _infer_threshold(self, sentence: str) -> tuple[str | None, str | None]:
        lowered = sentence.lower()
        if "high-high" in lowered or "hh" in lowered:
            return "HIGH_HIGH", "HIGH_HIGH"
        if "low-low" in lowered or "ll" in lowered:
            return "LOW_LOW", "LOW_LOW"
        if "high" in lowered and "level" in lowered:
            return "HIGH_LEVEL", "HIGH_LEVEL"
        if "low" in lowered and "level" in lowered:
            return "LOW_LEVEL", "LOW_LEVEL"
        if "normal" in lowered and "level" in lowered:
            return "NORMAL_LEVEL", "NORMAL_LEVEL"
        if "setpoint" in lowered or "sp" in lowered:
            return "SETPOINT", "SETPOINT"
        if "differential pressure" in lowered or "dp" in lowered:
            return "DP_SETPOINT", "DP_SETPOINT"
        if "header pressure low" in lowered or "pressure low" in lowered:
            return "HEADER_PRESSURE_LOW", "HEADER_PRESSURE_LOW"
        if "blanket" in lowered and "high" in lowered:
            return "BLANKET_HIGH", "BLANKET_HIGH"
        if "grit" in lowered and "high" in lowered:
            return "GRIT_HIGH", "GRIT_HIGH"
        if "ratio" in lowered or "proportional" in lowered:
            return "RATIO_SETPOINT", "RATIO_SETPOINT"
        if "startup" in lowered and "permissive" in lowered:
            return "STARTUP_PERMISSIVE", "STARTUP_PERMISSIVE"
        return None, None

    def _infer_condition_kind(self, sentence: str) -> str | None:
        lowered = sentence.lower()
        if "level" in lowered or "wet well" in lowered or "blanket" in lowered:
            return "level"
        if "differential pressure" in lowered or "dp" in lowered:
            return "differential_pressure"
        if "pressure" in lowered:
            return "pressure"
        if "analyzer" in lowered or "do " in lowered or "dissolved oxygen" in lowered:
            return "analyzer"
        if "turbidity" in lowered or "ph" in lowered or "chlorine" in lowered:
            return "analyzer"
        if "flow" in lowered:
            return "flow"
        if "timer" in lowered or "cycle" in lowered:
            return "timer"
        if "fault" in lowered or "fail" in lowered or "overload" in lowered or "vibration" in lowered:
            return "fault"
        if any(token in lowered for token in ("auto", "manual", "local", "remote")):
            return "mode"
        if any(token in lowered for token in ("startup", "shutdown", "sequence")):
            return "sequence_state"
        return "boolean_state"

    def _entity_match(
        self,
        sentence: str,
        entity_index: dict[str, dict],
        preferred_types: set[str] | None = None,
    ) -> tuple[str | None, str | None, str]:
        preferred_types = preferred_types or set()
        lowered = sentence.lower()

        for raw in self.tag_pattern.findall(sentence):
            token = self._normalize_token(raw)
            entity = entity_index.get(token)
            if entity is None:
                continue
            if preferred_types and entity.get("canonical_type") not in preferred_types:
                continue
            return entity["id"], entity.get("canonical_type"), "exact_tag"

        # Deterministic phrase aliases.
        phrase_aliases = {
            "air valve": {"control_valve"},
            "influent pump": {"pump"},
            "standby blower": {"blower"},
            "lag blower": {"blower"},
            "lead blower": {"blower"},
            "wet well level": {"level_transmitter", "level_switch"},
            "high differential pressure": {"differential_pressure_transmitter"},
            "do analyzer": {"analyzer"},
            "dissolved oxygen analyzer": {"analyzer"},
            "grit pump": {"pump"},
            "grit classifier": {"process_unit", "generic_device"},
            "polymer pump": {"pump", "chemical_system_device"},
            "coagulant pump": {"pump", "chemical_system_device"},
            "sludge pump": {"pump"},
            "ras pump": {"pump"},
            "was pump": {"pump"},
            "blanket analyzer": {"analyzer", "level_transmitter"},
        }

        for phrase, types in phrase_aliases.items():
            if phrase not in lowered:
                continue
            for entity in entity_index.values():
                ctype = entity.get("canonical_type")
                if ctype not in types:
                    continue
                if preferred_types and ctype not in preferred_types:
                    continue
                return entity["id"], ctype, "alias_match"

        for entity in entity_index.values():
            ctype = entity.get("canonical_type")
            if preferred_types and ctype not in preferred_types:
                continue
            aliases = [*entity.get("aliases", []), entity.get("display_name", "")]
            for alias in aliases:
                alias_text = str(alias).lower().replace("-", " ")
                if alias_text and alias_text in lowered:
                    return entity["id"], ctype, "alias_match"

        return None, None, "synthetic_placeholder"

    def _infer_action(self, sentence: str, rule_type: str) -> str:
        lowered = sentence.lower()
        if rule_type == "alarm":
            return "ALARM"
        if rule_type == "interlock":
            return "DISABLE"
        if rule_type == "lead_lag":
            return "SWITCH_TO_LAG" if "lag" in lowered or "standby" in lowered else "SWITCH_TO_LEAD"
        if rule_type == "mode":
            return "ENABLE"
        if rule_type == "sequence":
            return "SHUTDOWN" if "shutdown" in lowered else "ENABLE"
        if rule_type == "ratio_control":
            return "MODULATE"
        if "start" in lowered:
            return "START"
        if "stop" in lowered:
            return "STOP"
        if "open" in lowered:
            return "OPEN"
        if "close" in lowered:
            return "CLOSE"
        if "modulate" in lowered or "controls" in lowered:
            return "MODULATE"
        return "MODULATE" if rule_type in {"modulate", "setpoint_control", "pid_loop"} else "START"

    def extract(self, candidates: list[ControlRuleCandidate], entity_index: dict[str, dict]) -> tuple[list[ExtractedRuleDraft], list[str]]:
        drafts: list[ExtractedRuleDraft] = []
        warnings: list[str] = []

        for candidate in candidates:
            sentence = candidate.source_sentence
            lowered = sentence.lower()
            rule_type = candidate.rule_type
            action = self._infer_action(sentence, rule_type)
            operator = self._infer_operator(sentence)
            threshold, threshold_name = self._infer_threshold(sentence)
            condition_kind = self._infer_condition_kind(sentence)

            source_types = {
                "level": {"level_transmitter", "level_switch"},
                "pressure": {"pressure_transmitter"},
                "differential_pressure": {"differential_pressure_transmitter"},
                "analyzer": {"analyzer"},
                "flow": {"flow_transmitter"},
                "timer": set(),
                "fault": set(),
                "mode": set(),
                "sequence_state": set(),
                "boolean_state": set(),
            }
            target_types = {
                "START": {"pump", "blower", "process_unit", "generic_device"},
                "STOP": {"pump", "blower", "process_unit", "generic_device"},
                "OPEN": {"control_valve", "valve"},
                "CLOSE": {"control_valve", "valve"},
                "MODULATE": {"control_valve", "valve", "pump", "chemical_system_device"},
                "ALARM": {"process_unit", "pump", "tank", "basin", "clarifier", "analyzer", "blower"},
                "DISABLE": {"pump", "blower", "control_valve", "process_unit"},
                "SWITCH_TO_LEAD": {"pump", "blower"},
                "SWITCH_TO_LAG": {"pump", "blower"},
                "ENABLE": {"process_unit", "pump", "blower", "control_valve"},
                "SHUTDOWN": {"process_unit", "pump", "blower", "control_valve"},
                "HOLD": {"process_unit", "pump", "blower", "control_valve"},
            }

            source_tag, source_type, source_resolution = self._entity_match(
                sentence,
                entity_index,
                source_types.get(condition_kind or "", set()),
            )
            if source_tag is None and rule_type in {"start_stop", "modulate", "setpoint_control", "pid_loop", "ratio_control"}:
                source_tag, source_type, source_resolution = self._entity_match(sentence, entity_index)

            target_tag, target_type, target_resolution = self._entity_match(
                sentence,
                entity_index,
                target_types.get(action, set()),
            )

            unresolved: list[str] = []
            comments: list[str] = []
            renderable = True

            # Deterministic placeholders when narrative is explicit but numeric token missing.
            if threshold_name is None and condition_kind in {"level", "pressure", "differential_pressure", "analyzer", "flow"}:
                if condition_kind == "analyzer":
                    threshold_name = "DO_SETPOINT"
                    comments.append("TODO: exact analyzer setpoint not resolved; symbolic setpoint used.")
                elif condition_kind == "differential_pressure":
                    threshold_name = "DP_SETPOINT"
                    comments.append("TODO: exact differential pressure threshold not resolved; symbolic setpoint used.")
                elif condition_kind == "pressure":
                    threshold_name = "HEADER_PRESSURE_LOW"
                    comments.append("TODO: exact pressure threshold not resolved; symbolic setpoint used.")
                elif condition_kind == "level":
                    threshold_name = "LEVEL_SETPOINT"
                    comments.append("TODO: exact level threshold not resolved; symbolic setpoint used.")
                elif condition_kind == "flow":
                    threshold_name = "FLOW_SETPOINT"
                    comments.append("TODO: exact flow threshold not resolved; symbolic setpoint used.")

            if operator is None and threshold_name is not None:
                operator = "<" if "low" in lowered else ">="

            if source_tag is None:
                unresolved.append("source_tag")
            if target_tag is None and action in {"START", "STOP", "OPEN", "CLOSE", "MODULATE", "SWITCH_TO_LEAD", "SWITCH_TO_LAG", "DISABLE"}:
                unresolved.append("target_tag")
            if action == "ALARM" and source_tag is None:
                unresolved.append("alarm_trigger")

            confidence = candidate.confidence
            if source_tag:
                confidence += 0.12
            if target_tag:
                confidence += 0.12
            if threshold_name:
                confidence += 0.06
            confidence = max(0.2, min(0.99, confidence))

            if "process_unit" in {source_type, target_type}:
                # Prevent invalid condition expression on process unit labels.
                if source_type == "process_unit":
                    comments.append("TODO: source condition resolved to process unit; waiting for sensor tag refinement.")
                    renderable = False

            if "if true" in lowered:
                comments.append("TODO: rejected invalid unconditional narrative condition.")
                renderable = False

            explanation = f"Template-matched {rule_type} from narrative sentence"
            if source_tag:
                explanation += f"; source={source_tag}"
            if target_tag:
                explanation += f"; target={target_tag}"
            if threshold_name:
                explanation += f"; threshold={threshold_name}"

            if unresolved:
                warnings.append(f"Candidate unresolved fields ({','.join(unresolved)}): {sentence}")
                if rule_type not in {"sequence", "mode"}:
                    renderable = False

            if rule_type == "lead_lag":
                explicit_trigger = any(
                    token in lowered
                    for token in (
                        "pressure",
                        "level",
                        "runtime",
                        "duty",
                        "fault",
                        "trip",
                        "fail",
                        "timer",
                        "hour",
                        "header",
                    )
                )
                has_comparator = bool(operator and threshold_name)
                if not explicit_trigger and not has_comparator:
                    comments.append("TODO: lead/lag trigger unresolved; require explicit runtime/pressure/fault condition.")
                    unresolved.append("lead_lag_trigger")
                    renderable = False

            # Domain-specific deterministic template helpers.
            if "lead" in lowered and "pump" in lowered and action == "SWITCH_TO_LEAD":
                comments.append("TODO: lead pump rotation schedule placeholder derived from narrative.")
            if "lag" in lowered and "pump" in lowered and action == "SWITCH_TO_LAG":
                comments.append("TODO: lag pump staging placeholder derived from narrative.")
            if "proportional" in lowered or "ratio" in lowered:
                comments.append("TODO: exact ratio constant unresolved; ratio-control placeholder emitted.")

            drafts.append(
                ExtractedRuleDraft(
                    rule_group=candidate.rule_group,
                    rule_type=rule_type,
                    source_tag=source_tag,
                    source_type=source_type,
                    condition_kind=condition_kind,
                    operator=operator,
                    threshold=threshold_name,
                    threshold_name=threshold_name,
                    action=action,
                    target_tag=target_tag,
                    target_type=target_type,
                    secondary_target_tag=None,
                    mode="AUTO" if "auto" in lowered else "MANUAL" if "manual" in lowered else None,
                    priority=10 if rule_type in {"interlock", "alarm"} else 20,
                    confidence=confidence,
                    source_sentence=sentence,
                    source_page=candidate.source_page,
                    section_heading=candidate.section_heading,
                    explanation=explanation,
                    resolution_strategy=source_resolution if source_resolution != "synthetic_placeholder" else target_resolution,
                    renderable=renderable,
                    unresolved_tokens=unresolved,
                    comments=comments,
                    source_references=[
                        f"page:{candidate.source_page}" if candidate.source_page is not None else "page:unknown",
                        f"section:{candidate.section_heading or 'general'}",
                    ],
                )
            )

        self.logger.info("Control rule extraction: candidates=%s drafts=%s", len(candidates), len(drafts))
        return drafts, warnings


control_rule_extraction_service = ControlRuleExtractionService()
