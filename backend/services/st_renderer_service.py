from __future__ import annotations

from collections import defaultdict

from models.logic import ControlRule


GROUP_TITLES = {
    "influent_pump_station": "INFLUENT PUMP STATION",
    "screening": "FINE SCREENING",
    "grit_removal": "GRIT REMOVAL",
    "aeration": "AERATION BASIN",
    "blower_package": "BLOWER PACKAGE",
    "chemical_feed": "CHEMICAL FEED",
    "clarifier": "CLARIFIER / SLUDGE HANDLING",
    "startup_shutdown": "STARTUP / SHUTDOWN",
    "alarms": "ALARMS",
    "modes": "MODES",
    "general": "GENERAL",
}

GROUP_ORDER = [
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


class STRendererService:
    def render(
        self,
        rules: list[ControlRule],
        strategy: str,
        warnings: list[str],
        section_todos: dict[str, list[str]] | None = None,
    ) -> tuple[str, dict[str, list[ControlRule]]]:
        section_todos = section_todos or {}
        grouped: dict[str, list[ControlRule]] = defaultdict(list)
        for rule in rules:
            grouped[rule.rule_group].append(rule)

        lines = ["PROGRAM Main", f"(* Deterministic strategy: {strategy} *)", ""]

        for group in GROUP_ORDER:
            section_rules = sorted(grouped.get(group, []), key=lambda item: (item.priority, -item.confidence))
            has_section_todos = bool(section_todos.get(group))
            if not section_rules and not has_section_todos:
                continue

            lines.append("(* ===================================== *)")
            lines.append(f"(* {GROUP_TITLES.get(group, group.upper())} *)")
            lines.append("(* ===================================== *)")
            lines.append("")

            grounded_rules = [item for item in section_rules if not item.is_symbolic]
            symbolic_rules = [item for item in section_rules if item.is_symbolic and not item.st_preview.strip().startswith("(* TODO")]
            comment_rules = [item for item in section_rules if item.is_symbolic and item.st_preview.strip().startswith("(* TODO")]

            if grounded_rules:
                lines.append("(* Grounded Executable Rules *)")
                lines.append("")
                for rule in grounded_rules:
                    lines.append(f"(* {rule.display_text} *)")
                    for comment in rule.comments:
                        lines.append(f"(* TODO: {comment} *)")
                    lines.append(rule.st_preview)
                    lines.append("")

            if symbolic_rules:
                lines.append("(* Symbolic Structured Rules *)")
                lines.append("")
                for rule in symbolic_rules:
                    lines.append(f"(* {rule.display_text} *)")
                    for comment in rule.comments:
                        lines.append(f"(* TODO: {comment} *)")
                    lines.append(rule.st_preview)
                    lines.append("")

            if comment_rules:
                lines.append("(* Comment-Only Placeholders *)")
                lines.append("")
                for rule in comment_rules:
                    lines.append(f"(* {rule.display_text} *)")
                    for comment in rule.comments:
                        lines.append(f"(* TODO: {comment} *)")
                    lines.append(rule.st_preview)
                    lines.append("")

            for todo in section_todos.get(group, [])[:5]:
                lines.append(f"(* TODO: {todo} *)")
            if section_todos.get(group):
                lines.append("")

        if warnings:
            lines.append("(* ===================================== *)")
            lines.append("(* LOGIC WARNINGS *)")
            lines.append("(* ===================================== *)")
            for warning in warnings[:8]:
                lines.append(f"(* TODO: {warning} *)")
            lines.append("")

        lines.append("END_PROGRAM")
        return "\n".join(lines), dict(grouped)


st_renderer_service = STRendererService()
