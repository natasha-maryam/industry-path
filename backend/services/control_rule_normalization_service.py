from __future__ import annotations

import logging
from uuid import uuid4

from models.logic import ControlRule
from services.control_rule_extraction_service import ExtractedRuleDraft


class ControlRuleNormalizationService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _token(value: str | None, fallback: str) -> str:
        if not value:
            return fallback
        return value.upper().replace("-", "_")

    def _render_condition(self, rule: ControlRule) -> tuple[str | None, list[str]]:
        comments: list[str] = list(rule.comments)
        source = self._token(rule.source_tag, "")
        threshold = self._token(rule.threshold_name or rule.threshold, "")

        # Level switches are boolean triggers; do not render analog comparator logic for them.
        if source.startswith(("LSHH_", "LSLL_", "LSH_", "LSL_")) or rule.source_type == "level_switch":
            return source, comments

        if rule.condition_kind in {"mode", "sequence_state"}:
            if rule.mode:
                return f"MODE_{rule.mode.upper()}", comments
            comments.append("TODO: mode/sequence condition unresolved.")
            return None, comments

        if rule.condition_kind == "timer":
            return "TIMER_CYCLE_ELAPSED", comments

        if not source:
            comments.append("TODO: missing source tag; condition unresolved.")
            return None, comments

        if rule.source_type == "process_unit":
            comments.append("TODO: process unit cannot be used directly as boolean condition; map to sensor tag.")
            return None, comments

        if rule.action == "ALARM" and not (rule.operator and threshold):
            if threshold:
                op = rule.operator or ">="
                return f"{source} {op} {threshold}", comments
            comments.append("TODO: alarm trigger threshold unresolved.")
            return None, comments

        if rule.operator and threshold:
            return f"{source} {rule.operator} {threshold}", comments

        if rule.operator and not threshold:
            comments.append("TODO: operator present but threshold unresolved.")
            return None, comments

        if threshold and not rule.operator:
            op = "<" if "LOW" in threshold else ">="
            return f"{source} {op} {threshold}", comments

        # No explicit comparator for state/fault style logic.
        if rule.condition_kind in {"fault", "boolean_state"}:
            return source, comments

        comments.append("TODO: condition unresolved; symbolic placeholder not enough for renderable rule.")
        return None, comments

    def _display_text(self, rule: ControlRule, condition: str | None) -> str:
        lhs = condition or "TODO_CONDITION"
        target = self._token(rule.target_tag, "TODO_TARGET")
        return f"IF {lhs} THEN {rule.action} {target}"

    def _st_preview(self, rule: ControlRule, condition: str | None) -> str:
        target = self._token(rule.target_tag, "TODO_TARGET")
        if condition is None:
            todo = rule.comments[-1] if rule.comments else "Condition unresolved"
            return f"(* TODO: {todo} *)"

        if rule.action == "ALARM":
            hh_marker = next((item for item in rule.comments if item.startswith("__HH_START_PUMPS__:")), None)
            if hh_marker:
                pump_tokens = [self._token(token.strip(), "") for token in hh_marker.split(":", 1)[1].split(",") if token.strip()]
                lines = [f"IF {condition} THEN", f"    ALARM({target});"]
                for pump in pump_tokens:
                    lines.append(f"    START({pump});")
                lines.append("END_IF;")
                return "\n".join(lines)

        return f"IF {condition} THEN\n    {rule.action}({target});\nEND_IF;"

    def normalize(self, project_id: str, drafts: list[ExtractedRuleDraft]) -> list[ControlRule]:
        rules: list[ControlRule] = []

        for draft in drafts:
            rule = ControlRule(
                id=str(uuid4()),
                project_id=project_id,
                rule_group=draft.rule_group,  # type: ignore[arg-type]
                rule_type=draft.rule_type,  # type: ignore[arg-type]
                source_tag=draft.source_tag,
                source_type=draft.source_type,
                condition_kind=draft.condition_kind,  # type: ignore[arg-type]
                operator=draft.operator,  # type: ignore[arg-type]
                threshold=draft.threshold,
                threshold_name=draft.threshold_name,
                action=draft.action,  # type: ignore[arg-type]
                target_tag=draft.target_tag,
                target_type=draft.target_type,
                secondary_target_tag=draft.secondary_target_tag,
                mode=draft.mode,
                priority=draft.priority,
                confidence=draft.confidence,
                source_sentence=draft.source_sentence,
                source_page=draft.source_page,
                section_heading=draft.section_heading,
                explanation=draft.explanation,
                resolution_strategy=draft.resolution_strategy,
                renderable=draft.renderable,
                unresolved_tokens=list(draft.unresolved_tokens),
                comments=list(draft.comments),
                display_text="",
                st_preview="",
                source_references=draft.source_references,
            )

            condition, updated_comments = self._render_condition(rule)
            rule.comments = updated_comments
            if condition is None:
                rule.renderable = False

            rule.display_text = self._display_text(rule, condition)
            rule.st_preview = self._st_preview(rule, condition)
            rules.append(rule)

        self.logger.info("Control rule normalization: drafts=%s rules=%s", len(drafts), len(rules))
        return rules


control_rule_normalization_service = ControlRuleNormalizationService()
