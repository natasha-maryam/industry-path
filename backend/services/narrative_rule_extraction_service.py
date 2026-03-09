from __future__ import annotations

import logging
import re

from models.pipeline import (
    AlarmDefinition,
    ControlLoopDefinition,
    InterlockDefinition,
    ModeDefinition,
    SequenceDefinition,
)
from services.tag_normalization_service import tag_normalization_service


class NarrativeRuleExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def extract_rules(self, chunks) -> dict[str, list]:
        control_loops: list[ControlLoopDefinition] = []
        alarms: list[AlarmDefinition] = []
        interlocks: list[InterlockDefinition] = []
        sequences: list[SequenceDefinition] = []
        modes: list[ModeDefinition] = []

        for chunk in chunks:
            sentence = chunk.text.strip()
            if not sentence:
                continue

            tags = [item["normalized_tag"] for item in tag_normalization_service.detect_tags(sentence)]
            lowered = sentence.lower()

            if any(token in lowered for token in ("control", "lead/lag", "staging", "pid loop", "maintain")):
                control_loops.append(
                    ControlLoopDefinition(
                        name=self._derive_name(sentence, "control_loop"),
                        source_sentence=sentence,
                        page_number=chunk.page_number,
                        related_tags=tags,
                        confidence=0.88 if len(tags) >= 2 else 0.72,
                    )
                )

            if "alarm" in lowered:
                alarms.append(
                    AlarmDefinition(
                        name=self._derive_name(sentence, "alarm"),
                        source_sentence=sentence,
                        page_number=chunk.page_number,
                        related_tags=tags,
                        confidence=0.84 if tags else 0.65,
                    )
                )

            if any(token in lowered for token in ("interlock", "permissive", "trip")):
                interlocks.append(
                    InterlockDefinition(
                        name=self._derive_name(sentence, "interlock"),
                        source_sentence=sentence,
                        page_number=chunk.page_number,
                        related_tags=tags,
                        confidence=0.86 if tags else 0.68,
                    )
                )

            if "startup" in lowered or "start-up" in lowered:
                sequences.append(
                    SequenceDefinition(
                        sequence_type="startup",
                        source_sentence=sentence,
                        page_number=chunk.page_number,
                        related_tags=tags,
                    )
                )

            if "shutdown" in lowered:
                sequences.append(
                    SequenceDefinition(
                        sequence_type="shutdown",
                        source_sentence=sentence,
                        page_number=chunk.page_number,
                        related_tags=tags,
                    )
                )

            if any(token in lowered for token in ("auto", "manual", "mode", "fail-safe", "failsafe")):
                mode_name = "AUTO_MANUAL"
                if re.search(r"\bmanual\b", lowered) and not re.search(r"\bauto\b", lowered):
                    mode_name = "MANUAL"
                elif re.search(r"\bauto\b", lowered) and not re.search(r"\bmanual\b", lowered):
                    mode_name = "AUTO"
                modes.append(
                    ModeDefinition(
                        mode_name=mode_name,
                        source_sentence=sentence,
                        page_number=chunk.page_number,
                        related_tags=tags,
                        confidence=0.74 if tags else 0.62,
                    )
                )

        self.logger.info(
            "Narrative rules extracted: control_loops=%s alarms=%s interlocks=%s sequences=%s modes=%s",
            len(control_loops),
            len(alarms),
            len(interlocks),
            len(sequences),
            len(modes),
        )

        return {
            "control_loops": control_loops,
            "alarms": alarms,
            "interlocks": interlocks,
            "sequences": sequences,
            "modes": modes,
        }

    @staticmethod
    def _derive_name(sentence: str, fallback: str) -> str:
        compact = sentence.strip().replace("\n", " ")
        if not compact:
            return fallback
        return compact[:96]


narrative_rule_extraction_service = NarrativeRuleExtractionService()
