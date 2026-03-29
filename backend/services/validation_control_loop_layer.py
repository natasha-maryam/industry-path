from __future__ import annotations

import logging
import re

from models.document_pipeline import (
    DocumentParsingPipelineResult,
    PipelineControlLoopRecord,
    TuningDataRecord,
    ValidatedGraphRecord,
    ValidationControlLoopLayerResult,
)
from models.pipeline import InferredRelationship
from services.cross_validation_service import cross_validation_service
from services.graph_build_service import graph_build_service
from services.parser_relationship_graph_service import parser_relationship_graph_service
from services.graph_validation_service import graph_validation_service
from services.strict_control_loop_engine import strict_control_loop_engine


class ValidationControlLoopLayer:
    DEFAULT_VISIBLE_LOOP_CONFIDENCE_THRESHOLD = 0.84
    TUNING_BEHAVIOR_TERMS = {
        "unstable": r"\bunstable\b",
        "overshoot": r"\bovershoot(?:ing)?\b",
        "oscillation": r"\boscillat(?:ion|ing|es?)\b",
        "hunting": r"\bhunting\b",
        "noisy_response": r"\bnoisy\s+response\b|\bresponse\s+is\s+noisy\b",
    }
    TUNING_MODE_PATTERNS = {
        "auto": r"\bauto(?:matic)?\b",
        "manual": r"\bmanual\b",
    }
    SENSOR_TYPES = {
        "analyzer",
        "flow_transmitter",
        "level_transmitter",
        "level_switch",
        "pressure_transmitter",
        "differential_pressure_transmitter",
        "temperature_transmitter",
    }
    ACTUATOR_TYPES = {"pump", "valve", "control_valve", "blower", "chemical_system_device", "motor", "vfd"}

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def process(self, structured, semantic) -> ValidationControlLoopLayerResult:
        validated_relationships, validation_warnings, validation_low = graph_validation_service.validate(
            entities=semantic.entities,
            relationships=semantic.supported_relationships,
        )
        rejected_relationships = [*semantic.rejected_relationships, *validation_low]
        parser_graph = parser_relationship_graph_service.build_from_validated_relationships(
            semantic.entities,
            validated_relationships,
            metadata_by_entity=semantic.metadata_by_entity,
        )
        validated_graph = ValidatedGraphRecord(
            entities=semantic.entities,
            relationships=validated_relationships,
            rejected_relationships=rejected_relationships,
            parser_graph=parser_graph,
            warnings=[item.message for item in validation_warnings],
        )
        nodes, edges = graph_build_service.build(semantic.entities, validated_relationships, deep_metadata=semantic.metadata_by_entity)
        loop_candidates, traversal_warnings = strict_control_loop_engine.discover(
            entities=semantic.entities,
            relationships=validated_relationships,
            metadata_by_entity=semantic.metadata_by_entity,
            intents=semantic.normalized_intents,
        )
        control_loops, rejected_control_loops, loop_validation_debug = cross_validation_service.validate_loops(
            loop_candidates,
            semantic.entities,
        )
        tuning_data, tuning_warnings = self._detect_tuning_data(structured, control_loops)
        control_loops = self._apply_tuning_data(control_loops, tuning_data)
        rejected_control_loops = self._apply_tuning_data(rejected_control_loops, tuning_data)
        control_loops, hidden_control_loops, loop_validation_debug = self._partition_visible_loops(
            control_loops,
            loop_validation_debug,
            threshold=self.DEFAULT_VISIBLE_LOOP_CONFIDENCE_THRESHOLD,
        )
        rejected_control_loops = self._merge_rejected_loops(rejected_control_loops, hidden_control_loops)

        warnings = [item.message for item in validation_warnings]
        warnings.extend(traversal_warnings)
        warnings.extend(tuning_warnings)
        if hidden_control_loops:
            warnings.append(
                f"Hidden {len(hidden_control_loops)} low-confidence control loop candidates below visibility threshold {self.DEFAULT_VISIBLE_LOOP_CONFIDENCE_THRESHOLD:.2f}."
            )
        if not control_loops:
            warnings.append("Validation layer rejected weak loop candidates; no strict control loops detected.")

        self.logger.info(
            "Validation layer: validated_relationships=%s rejected_relationships=%s control_loops=%s tuning_data=%s",
            len(validated_relationships),
            len(rejected_relationships),
            len(control_loops),
            len(tuning_data),
        )
        return ValidationControlLoopLayerResult(
            validated_graph=validated_graph,
            nodes=nodes,
            edges=edges,
            control_loops=control_loops,
            rejected_control_loops=rejected_control_loops,
            loop_validation_debug=loop_validation_debug,
            tuning_data=tuning_data,
            low_confidence_relationships=rejected_relationships,
            warnings=warnings,
        )

    def _detect_tuning_data(self, structured, control_loops):
        warnings: list[str] = []
        if not control_loops:
            return [], warnings

        tuning_records: list[TuningDataRecord] = []
        for block in structured.blocks:
            text = self._block_tuning_text(block)
            lowered = text.lower()
            if "pid" not in lowered and all(token not in lowered for token in ("kp", "ki", "kd", "ti", "td", "proportional band", "reset", "rate", "auto", "manual", "unstable", "overshoot", "oscillat", "hunting", "noisy")):
                continue

            numeric_values = {
                "kp": self._extract_float(text, r"\bKp\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "ki": self._extract_float(text, r"\bKi\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "kd": self._extract_float(text, r"\bKd\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "reset_time": self._extract_float(text, r"\b(?:reset time|reset)\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "ti": self._extract_float(text, r"\bTi\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "td": self._extract_float(text, r"\bTd\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "proportional_band": self._extract_float(text, r"\b(?:PB|Proportional Band)\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "setpoint": self._extract_float(text, r"\b(?:SP|Setpoint)\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "output_min": self._extract_float(text, r"\bOutput Min\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
                "output_max": self._extract_float(text, r"\bOutput Max\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
            }
            populated_count = sum(1 for value in numeric_values.values() if value is not None)
            behavior_terms = self._extract_behavior_terms(text)
            mode = self._extract_mode(text)
            related_tags = sorted({match.group(1).upper().replace("_", "-") for match in re.finditer(r"\b([A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b", text, re.IGNORECASE)})
            related_loop = self._associate_tuning_loop(
                block=block,
                text=text,
                related_tags=related_tags,
                control_loops=control_loops,
            )

            if populated_count == 0 and not behavior_terms and mode is None:
                continue
            if related_loop is None:
                warnings.append(f"Rejected weak tuning data candidate from {block.file_name} page {block.page_number}.")
                continue

            completeness_signal = 0.2 if populated_count > 0 else 0.0
            parameter_signal = min(0.45, 0.11 * populated_count)
            behavior_signal = min(0.25, 0.08 * len(behavior_terms))
            mode_signal = 0.08 if mode else 0.0
            loop_signal = min(0.12, 0.03 * len([item for item in related_loop.chain if item]))
            tuning_confidence = min(0.99, completeness_signal + parameter_signal + behavior_signal + mode_signal + loop_signal)

            tuning_records.append(
                TuningDataRecord(
                    tuning_id=f"tuning:{block.block_id}",
                    loop_reference=related_loop.loop_id,
                    controller_tag=related_loop.controller_tag,
                    related_tags=related_tags,
                    kp=numeric_values["kp"],
                    ki=numeric_values["ki"],
                    kd=numeric_values["kd"],
                    reset_time=numeric_values["reset_time"],
                    ti=numeric_values["ti"],
                    td=numeric_values["td"],
                    proportional_band=numeric_values["proportional_band"],
                    mode=mode,
                    behavior_terms=behavior_terms,
                    setpoint=numeric_values["setpoint"],
                    output_min=numeric_values["output_min"],
                    output_max=numeric_values["output_max"],
                    source_section_reference=block.source_references[0] if block.source_references else block.block_id,
                    source_file_id=block.file_id,
                    source_file_name=block.file_name,
                    source_references=list(block.source_references),
                    source_block_id=block.block_id,
                    source_page=block.page_number,
                    source_text=text[:400],
                    confidence=round(tuning_confidence, 3),
                )
            )

        return sorted(tuning_records, key=lambda item: (item.loop_reference or "", item.source_page, item.tuning_id)), warnings

    @staticmethod
    def _apply_tuning_data(control_loops, tuning_data):
        tuning_by_loop: dict[str, dict[str, object]] = {}
        for item in tuning_data:
            if not item.loop_reference:
                continue
            current = tuning_by_loop.get(item.loop_reference)
            payload = {
                "kp": item.kp,
                "ki": item.ki,
                "kd": item.kd,
                "reset_time": item.reset_time if item.reset_time is not None else item.ti,
                "proportional_band": item.proportional_band,
                "mode": item.mode,
                "behavior_terms": list(item.behavior_terms),
                "source_references": list(item.source_references or ([item.source_section_reference] if item.source_section_reference else [])),
                "confidence": float(item.confidence),
            }
            if current is None:
                tuning_by_loop[item.loop_reference] = payload
                continue
            for key in ("kp", "ki", "kd", "reset_time", "proportional_band", "mode"):
                if current.get(key) in (None, "") and payload.get(key) not in (None, ""):
                    current[key] = payload[key]
            current["behavior_terms"] = sorted(set([*current.get("behavior_terms", []), *payload.get("behavior_terms", [])]))
            current["source_references"] = sorted(set([*current.get("source_references", []), *payload.get("source_references", [])]))
            current["confidence"] = max(float(current.get("confidence", 0.0)), float(payload["confidence"]))

        updated = []
        for loop in control_loops:
            tuning_payload = tuning_by_loop.get(loop.loop_id, {})
            tuning_confidence = max(float(loop.tuning_confidence or 0.0), float(tuning_payload.get("confidence", 0.0)))
            updated.append(
                loop.model_copy(
                    update={
                        "tuning": {
                            "kp": tuning_payload.get("kp"),
                            "ki": tuning_payload.get("ki"),
                            "kd": tuning_payload.get("kd"),
                            "reset_time": tuning_payload.get("reset_time"),
                            "proportional_band": tuning_payload.get("proportional_band"),
                            "mode": tuning_payload.get("mode"),
                            "behavior_terms": tuning_payload.get("behavior_terms", []),
                            "source_references": tuning_payload.get("source_references", []),
                        }
                        if tuning_payload
                        else {},
                        "tuning_confidence": round(tuning_confidence, 3),
                    }
                )
            )
        return updated

    @classmethod
    def _extract_behavior_terms(cls, text: str) -> list[str]:
        found: list[str] = []
        for label, pattern in cls.TUNING_BEHAVIOR_TERMS.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(label)
        return sorted(found)

    @classmethod
    def _extract_mode(cls, text: str) -> str | None:
        for label, pattern in cls.TUNING_MODE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    def _associate_tuning_loop(self, *, block, text: str, related_tags: list[str], control_loops: list[PipelineControlLoopRecord]):
        candidates: list[tuple[tuple[object, ...], PipelineControlLoopRecord]] = []
        normalized_text = text.upper()
        for loop in control_loops:
            chain_tags = [tag for tag in [loop.sensor_tag, loop.controller_tag, loop.actuator_tag, loop.process_node] if tag]
            overlap = len({tag for tag in related_tags if tag in set(chain_tags)})
            text_mentions = sum(1 for tag in chain_tags if tag and tag.upper() in normalized_text)
            page_distance = self._loop_page_distance(loop, block.page_number)
            source_ref_match = any(ref in set(block.source_references) for ref in (loop.source_texts or []))
            rank = (
                -(overlap * 3 + text_mentions),
                0 if source_ref_match else 1,
                page_distance,
                -float(loop.confidence),
                loop.loop_id,
            )
            candidates.append((rank, loop))
        if not candidates:
            return None
        best_rank, best_loop = sorted(candidates, key=lambda item: item[0])[0]
        if best_rank[0] == 0 and best_rank[1] == 1 and best_rank[2] > 2:
            return None
        return best_loop

    @staticmethod
    def _loop_page_distance(loop: PipelineControlLoopRecord, page_number: int) -> int:
        references = loop.source_texts or []
        pages: list[int] = []
        for reference in references:
            match = re.search(r":p(\d+)\b", reference, re.IGNORECASE)
            if match:
                pages.append(int(match.group(1)))
        if not pages:
            return 0
        return min(abs(item - page_number) for item in pages)

    @staticmethod
    def _block_tuning_text(block) -> str:
        parts: list[str] = []
        if getattr(block, "text", None):
            parts.append(block.text)
        for row in getattr(block, "table_rows", []) or []:
            flattened = " ".join(str(cell) for cell in row if cell not in (None, ""))
            if flattened:
                parts.append(flattened)
        return "\n".join(parts)

    @staticmethod
    def _merge_rejected_loops(existing, hidden):
        merged: dict[tuple[str, str, str], PipelineControlLoopRecord] = {}
        for item in [*existing, *hidden]:
            key = (item.sensor_tag, item.actuator_tag, item.process_node)
            current = merged.get(key)
            if current is None or item.confidence >= current.confidence:
                merged[key] = item
        return sorted(merged.values(), key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node))

    @staticmethod
    def _partition_visible_loops(control_loops, loop_validation_debug, *, threshold: float):
        hidden_ids: set[str] = set()
        visible: list[PipelineControlLoopRecord] = []
        hidden: list[PipelineControlLoopRecord] = []
        for loop in sorted(control_loops, key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node)):
            if float(loop.confidence) >= threshold:
                visible.append(loop)
            else:
                hidden.append(loop)
                hidden_ids.add(loop.loop_id)

        updated_debug = []
        for item in loop_validation_debug:
            hidden_candidate = item.candidate_id in hidden_ids
            reasons = list(item.rejection_reasons)
            if hidden_candidate and "below_visibility_threshold" not in reasons:
                reasons.append("below_visibility_threshold")
            updated_debug.append(
                item.model_copy(
                    update={
                        "visible_by_default": not hidden_candidate,
                        "visibility_threshold": threshold,
                        "rejection_reasons": reasons,
                    }
                )
            )

        return visible, hidden, sorted(updated_debug, key=lambda item: (item.visible_by_default is False, item.process_node, item.sensor_tag, item.actuator_tag))

    @staticmethod
    def _extract_float(text: str, pattern: str) -> float | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            return None
        return float(match.group(1))

    @staticmethod
    def _tag_pattern_support(source_tag: str, target_tag: str, intent_type) -> bool:
        if intent_type is None:
            return False
        source_digits = "".join(re.findall(r"\d+", source_tag))
        target_digits = "".join(re.findall(r"\d+", target_tag))
        return bool(source_digits and target_digits and source_digits == target_digits)


validation_control_loop_layer = ValidationControlLoopLayer()
