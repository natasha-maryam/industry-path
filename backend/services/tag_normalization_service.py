from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TagFamily:
    family: str
    canonical_prefix: str
    canonical_type: str
    pattern: re.Pattern[str]


class TagNormalizationService:
    """Detects, normalizes, and classifies engineering tags from raw text snippets."""

    def __init__(self) -> None:
        self.families: list[TagFamily] = [
            TagFamily("DPIT", "DPIT", "differential_pressure_transmitter", re.compile(r"\bDPIT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("LSLL", "LSLL", "level_switch", re.compile(r"\bLSLL[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("LSHH", "LSHH", "level_switch", re.compile(r"\bLSHH[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("LSL", "LSL", "level_switch", re.compile(r"\bLSL[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("LSH", "LSH", "level_switch", re.compile(r"\bLSH[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("FCV", "FCV", "control_valve", re.compile(r"\bFCV[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("FIT", "FIT", "flow_transmitter", re.compile(r"\bFIT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("FT", "FT", "flow_transmitter", re.compile(r"\bFT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("LIT", "LIT", "level_transmitter", re.compile(r"\bLIT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("LT", "LT", "level_transmitter", re.compile(r"\bLT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("PIT", "PIT", "pressure_transmitter", re.compile(r"\bPIT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("PT", "PT", "pressure_transmitter", re.compile(r"\bPT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("AIT", "AIT", "analyzer", re.compile(r"\bAIT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("AI", "AI", "analyzer", re.compile(r"\bAI[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("BL", "BL", "blower", re.compile(r"\bBL[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("PMP", "PMP", "pump", re.compile(r"\bPMP[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("P", "P", "pump", re.compile(r"\bP[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("XV", "XV", "valve", re.compile(r"\bXV[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("MOV", "MOV", "valve", re.compile(r"\bMOV[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("VAL", "VAL", "valve", re.compile(r"\bVAL[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("TK", "TK", "tank", re.compile(r"\bTK[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("T", "T", "tank", re.compile(r"\bT[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("BAS", "BAS", "basin", re.compile(r"\bBAS[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
            TagFamily("CL", "CL", "clarifier", re.compile(r"\bCL[-_ ]?(\d{2,5})\b", re.IGNORECASE)),
        ]

    @staticmethod
    def normalize_tag(prefix: str, number: str) -> str:
        clean_num = re.sub(r"\D", "", number)
        return f"{prefix.upper()}-{clean_num}"

    def detect_tags(self, text: str) -> list[dict[str, str]]:
        detections: list[dict[str, str]] = []
        for family in self.families:
            for match in family.pattern.finditer(text):
                raw = match.group(0)
                number = match.group(1)
                normalized = self.normalize_tag(family.canonical_prefix, number)
                detections.append(
                    {
                        "raw_tag": raw,
                        "normalized_tag": normalized,
                        "family": family.family,
                        "canonical_type": family.canonical_type,
                    }
                )
        return detections


tag_normalization_service = TagNormalizationService()
