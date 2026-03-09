from __future__ import annotations

import logging
import re
from uuid import uuid4

from models.logic import ControlRuleCandidate, NarrativeSentence, RuleType


class ControlRuleCandidateService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._patterns: list[tuple[RuleType, re.Pattern[str], str, float]] = [
            ("pid_loop", re.compile(r"\bpid\b|\bsetpoint\b", re.IGNORECASE), "pid/setpoint marker", 0.76),
            ("start_stop", re.compile(r"\b(if|when|upon)\b.*\b(start|stop)\b", re.IGNORECASE), "if-when start/stop clause", 0.86),
            ("start_stop", re.compile(r"\bhigh\b.*\b(start|starts)\b|\blow\b.*\b(stop|stops)\b", re.IGNORECASE), "high/low level start-stop", 0.83),
            ("open_close", re.compile(r"\b(open|close)\b", re.IGNORECASE), "open/close action", 0.8),
            ("modulate", re.compile(r"\b(controls|modulate|modulates)\b", re.IGNORECASE), "control/modulate phrase", 0.82),
            ("alarm", re.compile(r"\balarm\b|\bhigh-high\b|\blow-low\b", re.IGNORECASE), "alarm phrase", 0.81),
            ("interlock", re.compile(r"\binterlock\b|\bprevents\b|\bmust\b", re.IGNORECASE), "interlock/permissive phrase", 0.79),
            ("lead_lag", re.compile(r"\blead\b|\blag\b|\bstandby\b|\brotate\b", re.IGNORECASE), "lead-lag/standby phrase", 0.8),
            ("mode", re.compile(r"\bauto\b|\bmanual\b|\boverride\b|\blocal\b|\bremote\b", re.IGNORECASE), "mode switch phrase", 0.78),
            ("setpoint_control", re.compile(r"\bsetpoint\b|\bmaintain\b|\bhold\b", re.IGNORECASE), "setpoint control phrase", 0.77),
            ("sequence", re.compile(r"\bstartup\b|\bshutdown\b|\bemergency\b", re.IGNORECASE), "sequence phrase", 0.75),
            ("ratio_control", re.compile(r"\bproportional\b|\bratio\b|\bdosing\b", re.IGNORECASE), "ratio/proportional phrase", 0.78),
        ]

    @staticmethod
    def _infer_rule_group(section_heading: str | None, sentence: str) -> str:
        corpus = f"{section_heading or ''} {sentence}".lower()
        if any(token in corpus for token in ("influent", "wet well", "pump station")):
            return "influent_pump_station"
        if any(token in corpus for token in ("screen", "screening", "differential pressure")):
            return "screening"
        if "grit" in corpus:
            return "grit_removal"
        if any(token in corpus for token in ("aeration", "dissolved oxygen", "do analyzer", "air valve")):
            return "aeration"
        if any(token in corpus for token in ("blower", "header pressure", "air header")):
            return "blower_package"
        if any(token in corpus for token in ("chemical", "dosing", "ratio")):
            return "chemical_feed"
        if any(token in corpus for token in ("clarifier", "sludge", "blanket")):
            return "clarifier"
        if any(token in corpus for token in ("startup", "shutdown", "emergency")):
            return "startup_shutdown"
        if "alarm" in corpus:
            return "alarms"
        if any(token in corpus for token in ("auto", "manual", "local", "remote")):
            return "modes"
        return "general"

    def detect(self, project_id: str, sentences: list[NarrativeSentence]) -> list[ControlRuleCandidate]:
        candidates: list[ControlRuleCandidate] = []

        for sentence in sentences:
            lowered = sentence.text.lower()
            matched: list[tuple[RuleType, str, float]] = []
            for rule_type, pattern, reason, confidence in self._patterns:
                if pattern.search(sentence.text):
                    if rule_type == "mode":
                        meaningful_mode = any(token in lowered for token in ("switch", "command", "enable", "disable", "only when", "interlock"))
                        if not meaningful_mode:
                            continue
                    if rule_type == "sequence":
                        meaningful_sequence = any(token in lowered for token in ("step", "permissive", "complete", "trip", "shutdown", "emergency"))
                        if not meaningful_sequence:
                            continue
                    matched.append((rule_type, reason, confidence))

            for rule_type, reason, confidence in matched:
                candidates.append(
                    ControlRuleCandidate(
                        id=str(uuid4()),
                        project_id=project_id,
                        sentence_id=sentence.id,
                        rule_type=rule_type,
                        source_sentence=sentence.text,
                        source_page=sentence.page_number,
                        section_heading=sentence.section_heading,
                        rule_group=self._infer_rule_group(sentence.section_heading, sentence.text),
                        confidence=confidence,
                        reasons=[reason],
                    )
                )

        self.logger.info("Control rule candidate detection: sentences=%s candidates=%s", len(sentences), len(candidates))
        return candidates


control_rule_candidate_service = ControlRuleCandidateService()
