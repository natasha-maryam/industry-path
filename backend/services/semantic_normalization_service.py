from __future__ import annotations

import re


class SemanticNormalizationService:
    TAG_FAMILY_HINTS = {
        "flow_control": ("FIT", "FT", "FCV"),
        "level_control": ("LIT", "LT", "LS", "LSH", "LSL"),
        "pressure_control": ("PIT", "PT", "DPIT", "PCV"),
        "temperature_control": ("TIT", "TT", "TCV"),
    }

    def __init__(self) -> None:
        self.verb_normalization = {
            "maintains": "controls",
            "maintain": "controls",
            "regulates": "controls",
            "regulate": "controls",
            "controls": "controls",
            "control": "controls",
            "modulates": "controls",
            "modulate": "controls",
            "drives": "controls",
            "drive": "controls",
        }
        self.intent_patterns: list[tuple[re.Pattern[str], str]] = [
            (re.compile(r"\b(?:controls?|maintains?|regulates?)\s+flow\b", re.IGNORECASE), "flow_control"),
            (re.compile(r"\b(?:controls?|maintains?|regulates?)\s+level\b", re.IGNORECASE), "level_control"),
            (re.compile(r"\b(?:controls?|maintains?|regulates?)\s+pressure\b", re.IGNORECASE), "pressure_control"),
            (re.compile(r"\b(?:controls?|maintains?|regulates?)\s+temperature\b", re.IGNORECASE), "temperature_control"),
        ]

    def normalize_verb(self, text: str) -> str | None:
        lowered = text.lower()
        for raw, normalized in self.verb_normalization.items():
            if re.search(rf"\b{re.escape(raw)}\b", lowered):
                return normalized
        return None

    def detect_intent_type(self, text: str, related_tags: list[str] | None = None) -> str | None:
        for pattern, intent_type in self.intent_patterns:
            if pattern.search(text):
                return intent_type

        lowered = text.lower()
        if "flow" in lowered:
            return "flow_control"
        if "level" in lowered:
            return "level_control"
        if "pressure" in lowered:
            return "pressure_control"
        if "temperature" in lowered:
            return "temperature_control"

        for tag in related_tags or []:
            prefix = str(tag).split("-")[0].upper()
            for intent_type, families in self.TAG_FAMILY_HINTS.items():
                if any(prefix.startswith(family) for family in families):
                    return intent_type
        return None


semantic_normalization_service = SemanticNormalizationService()
