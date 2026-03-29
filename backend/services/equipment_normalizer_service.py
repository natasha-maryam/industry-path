from __future__ import annotations

import re
from dataclasses import dataclass

from models.document_pipeline import EquipmentNormalizationResult


@dataclass(frozen=True)
class _PatternRule:
    source: str
    label: str
    pattern: re.Pattern[str]
    normalized_equipment: str
    normalized_type: str
    confidence: float
    specificity: int


class EquipmentNormalizerService:
    def __init__(self) -> None:
        self._tag_rules: list[_PatternRule] = [
            _PatternRule("tag", "tag:FIT", re.compile(r"^FIT[-_]?(\d+)", re.IGNORECASE), "flow_transmitter", "flow_transmitter", 0.99, 120),
            _PatternRule("tag", "tag:FT", re.compile(r"^FT[-_]?(\d+)", re.IGNORECASE), "flow_transmitter", "flow_transmitter", 0.96, 110),
            _PatternRule("tag", "tag:LIT", re.compile(r"^LIT[-_]?(\d+)", re.IGNORECASE), "level_transmitter", "level_transmitter", 0.99, 120),
            _PatternRule("tag", "tag:LT", re.compile(r"^LT[-_]?(\d+)", re.IGNORECASE), "level_transmitter", "level_transmitter", 0.96, 110),
            _PatternRule("tag", "tag:PIT", re.compile(r"^PIT[-_]?(\d+)", re.IGNORECASE), "pressure_transmitter", "pressure_transmitter", 0.99, 120),
            _PatternRule("tag", "tag:PT", re.compile(r"^PT[-_]?(\d+)", re.IGNORECASE), "pressure_transmitter", "pressure_transmitter", 0.96, 110),
            _PatternRule("tag", "tag:DPIT", re.compile(r"^DPIT[-_]?(\d+)", re.IGNORECASE), "pressure_transmitter", "differential_pressure_transmitter", 0.98, 125),
            _PatternRule("tag", "tag:TIT", re.compile(r"^TIT[-_]?(\d+)", re.IGNORECASE), "temperature_transmitter", "temperature_transmitter", 0.99, 120),
            _PatternRule("tag", "tag:TT", re.compile(r"^TT[-_]?(\d+)", re.IGNORECASE), "temperature_transmitter", "temperature_transmitter", 0.96, 110),
            _PatternRule("tag", "tag:AIT", re.compile(r"^AIT[-_]?(\d+)", re.IGNORECASE), "analyzer", "analyzer", 0.98, 120),
            _PatternRule("tag", "tag:AI", re.compile(r"^AI[-_]?(\d+)", re.IGNORECASE), "analyzer", "analyzer", 0.94, 110),
            _PatternRule("tag", "tag:FCV", re.compile(r"^FCV[-_]?(\d+)", re.IGNORECASE), "flow_control_valve", "control_valve", 0.98, 130),
            _PatternRule("tag", "tag:PCV", re.compile(r"^PCV[-_]?(\d+)", re.IGNORECASE), "pressure_control_valve", "control_valve", 0.98, 130),
            _PatternRule("tag", "tag:TCV", re.compile(r"^TCV[-_]?(\d+)", re.IGNORECASE), "temperature_control_valve", "control_valve", 0.98, 130),
            _PatternRule("tag", "tag:CV", re.compile(r"^CV[-_]?(\d+)", re.IGNORECASE), "control_valve", "control_valve", 0.94, 118),
            _PatternRule("tag", "tag:XV", re.compile(r"^XV[-_]?(\d+)", re.IGNORECASE), "valve", "valve", 0.92, 105),
            _PatternRule("tag", "tag:MOV", re.compile(r"^MOV[-_]?(\d+)", re.IGNORECASE), "motor_operated_valve", "valve", 0.92, 108),
            _PatternRule("tag", "tag:PMP", re.compile(r"^PMP[-_]?(\d+)", re.IGNORECASE), "pump", "pump", 0.97, 115),
            _PatternRule("tag", "tag:PUMP", re.compile(r"^PUMP[-_]?(\d+)", re.IGNORECASE), "pump", "pump", 0.97, 115),
            _PatternRule("tag", "tag:BAS", re.compile(r"^BAS[-_]?(\d+)", re.IGNORECASE), "basin", "basin", 0.94, 100),
            _PatternRule("tag", "tag:TK", re.compile(r"^TK[-_]?(\d+)", re.IGNORECASE), "tank", "tank", 0.94, 100),
            _PatternRule("tag", "tag:CL", re.compile(r"^CL[-_]?(\d+)", re.IGNORECASE), "clarifier", "clarifier", 0.92, 98),
            _PatternRule("tag", "tag:RCT", re.compile(r"^RCT[-_]?(\d+)", re.IGNORECASE), "reactor", "reactor", 0.92, 98),
            _PatternRule("tag", "tag:FIL", re.compile(r"^FIL[-_]?(\d+)", re.IGNORECASE), "filter", "filter", 0.92, 98),
            _PatternRule("tag", "tag:HX", re.compile(r"^HX[-_]?(\d+)", re.IGNORECASE), "heat_exchanger", "heat_exchanger", 0.92, 98),
            _PatternRule("tag", "tag:BLR", re.compile(r"^BLR[-_]?(\d+)", re.IGNORECASE), "boiler", "boiler", 0.92, 98),
            _PatternRule("tag", "tag:CLR", re.compile(r"^CLR[-_]?(\d+)", re.IGNORECASE), "cooler", "cooler", 0.9, 95),
            _PatternRule("tag", "tag:BL", re.compile(r"^BL[-_]?(\d+)", re.IGNORECASE), "blower", "blower", 0.92, 102),
            _PatternRule("tag", "tag:CMP", re.compile(r"^CMP[-_]?(\d+)", re.IGNORECASE), "compressor", "compressor", 0.92, 102),
            _PatternRule("tag", "tag:MTR", re.compile(r"^MTR[-_]?(\d+)", re.IGNORECASE), "motor", "motor", 0.92, 102),
            _PatternRule("tag", "tag:VFD", re.compile(r"^VFD[-_]?(\d+)", re.IGNORECASE), "vfd", "vfd", 0.92, 102),
            _PatternRule("tag", "tag:PNL", re.compile(r"^PNL[-_]?(\d+)", re.IGNORECASE), "panel", "panel", 0.9, 95),
            _PatternRule("tag", "tag:PIPE", re.compile(r"^PIPE[-_]?(\d+)", re.IGNORECASE), "pipe", "pipe", 0.9, 95),
            _PatternRule("tag", "tag:MAN", re.compile(r"^MAN[-_]?(\d+)", re.IGNORECASE), "manifold", "manifold", 0.9, 95),
        ]
        self._phrase_rules: list[_PatternRule] = [
            _PatternRule("phrase", "phrase:pressure control valve", re.compile(r"\bpressure control valve\b", re.IGNORECASE), "pressure_control_valve", "control_valve", 0.97, 130),
            _PatternRule("phrase", "phrase:temperature control valve", re.compile(r"\btemperature control valve\b", re.IGNORECASE), "temperature_control_valve", "control_valve", 0.97, 130),
            _PatternRule("phrase", "phrase:flow control valve", re.compile(r"\bflow control valve\b", re.IGNORECASE), "flow_control_valve", "control_valve", 0.97, 130),
            _PatternRule("phrase", "phrase:control valve", re.compile(r"\bcontrol valve\b", re.IGNORECASE), "control_valve", "control_valve", 0.95, 120),
            _PatternRule("phrase", "phrase:flow transmitter", re.compile(r"\b(flow transmitter|flow meter|mag meter)\b", re.IGNORECASE), "flow_transmitter", "flow_transmitter", 0.95, 118),
            _PatternRule("phrase", "phrase:level transmitter", re.compile(r"\b(level transmitter|level sensor)\b", re.IGNORECASE), "level_transmitter", "level_transmitter", 0.95, 118),
            _PatternRule("phrase", "phrase:pressure transmitter", re.compile(r"\b(pressure transmitter|pressure sensor)\b", re.IGNORECASE), "pressure_transmitter", "pressure_transmitter", 0.95, 118),
            _PatternRule("phrase", "phrase:temperature transmitter", re.compile(r"\b(temperature transmitter|temperature sensor)\b", re.IGNORECASE), "temperature_transmitter", "temperature_transmitter", 0.95, 118),
            _PatternRule("phrase", "phrase:analyzer", re.compile(r"\b(analyzer|analyser)\b", re.IGNORECASE), "analyzer", "analyzer", 0.94, 110),
            _PatternRule("phrase", "phrase:compressor", re.compile(r"\b(air compressor|compressor)\b", re.IGNORECASE), "compressor", "compressor", 0.93, 108),
            _PatternRule("phrase", "phrase:blower", re.compile(r"\b(air blower|blower)\b", re.IGNORECASE), "blower", "blower", 0.93, 108),
            _PatternRule("phrase", "phrase:heat exchanger", re.compile(r"\b(heat exchanger|hx)\b", re.IGNORECASE), "heat_exchanger", "heat_exchanger", 0.93, 108),
            _PatternRule("phrase", "phrase:boiler", re.compile(r"\bboiler\b", re.IGNORECASE), "boiler", "boiler", 0.92, 104),
            _PatternRule("phrase", "phrase:cooler", re.compile(r"\b(cooler|chiller)\b", re.IGNORECASE), "cooler", "cooler", 0.92, 104),
            _PatternRule("phrase", "phrase:clarifier", re.compile(r"\bclarifier\b", re.IGNORECASE), "clarifier", "clarifier", 0.92, 104),
            _PatternRule("phrase", "phrase:reactor", re.compile(r"\breactor\b", re.IGNORECASE), "reactor", "reactor", 0.92, 104),
            _PatternRule("phrase", "phrase:filter", re.compile(r"\b(filter|filtration unit|media filter|sand filter)\b", re.IGNORECASE), "filter", "filter", 0.92, 104),
            _PatternRule("phrase", "phrase:basin", re.compile(r"\b(aeration basin|basin)\b", re.IGNORECASE), "basin", "basin", 0.92, 104),
            _PatternRule("phrase", "phrase:tank", re.compile(r"\b(storage tank|mix tank|tank)\b", re.IGNORECASE), "tank", "tank", 0.92, 104),
            _PatternRule("phrase", "phrase:pump", re.compile(r"\b(centrifugal pump|pump)\b", re.IGNORECASE), "pump", "pump", 0.92, 104),
            _PatternRule("phrase", "phrase:valve", re.compile(r"\b(isolation valve|butterfly valve|gate valve|valve)\b", re.IGNORECASE), "valve", "valve", 0.9, 100),
            _PatternRule("phrase", "phrase:motor", re.compile(r"\b(motor|drive motor)\b", re.IGNORECASE), "motor", "motor", 0.9, 100),
            _PatternRule("phrase", "phrase:vfd", re.compile(r"\b(variable frequency drive|vfd)\b", re.IGNORECASE), "vfd", "vfd", 0.9, 100),
            _PatternRule("phrase", "phrase:panel", re.compile(r"\b(control panel|mcc panel|mcc|plc panel|panel)\b", re.IGNORECASE), "panel", "panel", 0.9, 100),
            _PatternRule("phrase", "phrase:pipe", re.compile(r"\b(pipe|piping|line)\b", re.IGNORECASE), "pipe", "pipe", 0.88, 92),
            _PatternRule("phrase", "phrase:manifold", re.compile(r"\bmanifold\b", re.IGNORECASE), "manifold", "manifold", 0.88, 92),
        ]

    def normalize(self, *, tag_name: str | None = None, description: str | None = None, fallback_type: str | None = None) -> EquipmentNormalizationResult:
        normalized_tag = self._normalize_token(tag_name)
        description_text = str(description or "")
        candidates: list[tuple[int, float, int, EquipmentNormalizationResult]] = []

        for index, rule in enumerate(self._tag_rules):
            if normalized_tag and rule.pattern.search(normalized_tag):
                candidates.append(
                    (
                        rule.specificity,
                        rule.confidence,
                        -index,
                        EquipmentNormalizationResult(
                            normalized_equipment=rule.normalized_equipment,
                            normalized_type=rule.normalized_type,
                            matched_pattern=rule.label,
                            confidence=rule.confidence,
                        ),
                    )
                )

        for index, rule in enumerate(self._phrase_rules):
            if description_text and rule.pattern.search(description_text):
                candidates.append(
                    (
                        rule.specificity,
                        rule.confidence,
                        -(1000 + index),
                        EquipmentNormalizationResult(
                            normalized_equipment=rule.normalized_equipment,
                            normalized_type=rule.normalized_type,
                            matched_pattern=rule.label,
                            confidence=rule.confidence,
                        ),
                    )
                )

        fallback = self._fallback_result(fallback_type)
        if fallback is not None:
            candidates.append((70, fallback.confidence, -2000, fallback))

        if candidates:
            return sorted(candidates, key=lambda item: (item[0], item[1], item[2]), reverse=True)[0][3]

        return EquipmentNormalizationResult(
            normalized_equipment="generic_equipment",
            normalized_type="generic_equipment",
            matched_pattern="fallback:generic_equipment",
            confidence=0.55,
        )

    def _fallback_result(self, fallback_type: str | None) -> EquipmentNormalizationResult | None:
        normalized = self._normalize_token(fallback_type)
        mapping = {
            "pump": ("pump", "pump"),
            "valve": ("valve", "valve"),
            "control_valve": ("control_valve", "control_valve"),
            "tank": ("tank", "tank"),
            "basin": ("basin", "basin"),
            "clarifier": ("clarifier", "clarifier"),
            "reactor": ("reactor", "reactor"),
            "filter": ("filter", "filter"),
            "heat_exchanger": ("heat_exchanger", "heat_exchanger"),
            "boiler": ("boiler", "boiler"),
            "cooler": ("cooler", "cooler"),
            "blower": ("blower", "blower"),
            "compressor": ("compressor", "compressor"),
            "flow_transmitter": ("flow_transmitter", "flow_transmitter"),
            "level_transmitter": ("level_transmitter", "level_transmitter"),
            "pressure_transmitter": ("pressure_transmitter", "pressure_transmitter"),
            "differential_pressure_transmitter": ("pressure_transmitter", "differential_pressure_transmitter"),
            "temperature_transmitter": ("temperature_transmitter", "temperature_transmitter"),
            "analyzer": ("analyzer", "analyzer"),
            "motor": ("motor", "motor"),
            "vfd": ("vfd", "vfd"),
            "panel": ("panel", "panel"),
            "pipe": ("pipe", "pipe"),
            "manifold": ("manifold", "manifold"),
            "generic_device": ("generic_equipment", "generic_equipment"),
            "generic_equipment": ("generic_equipment", "generic_equipment"),
            "process_unit": ("generic_equipment", "generic_equipment"),
        }
        if normalized not in mapping:
            return None
        equipment, normalized_type = mapping[normalized]
        return EquipmentNormalizationResult(
            normalized_equipment=equipment,
            normalized_type=normalized_type,
            matched_pattern=f"fallback:{normalized}",
            confidence=0.72,
        )

    @staticmethod
    def _normalize_token(value: str | None) -> str:
        return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


equipment_normalizer_service = EquipmentNormalizerService()
