from __future__ import annotations

import logging
import re

from models.document_pipeline import (
    LoopValidationDebugRecord,
    NormalizedIntentRecord,
    PipelineControlLoopRecord,
    RelationshipValidationDebugRecord,
    ValidationSignalRecord,
)
from models.pipeline import EngineeringEntity, InferredRelationship


class CrossValidationService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def validate_relationships(
        self,
        candidates: list[InferredRelationship],
        entities: list[EngineeringEntity],
        intents: list[NormalizedIntentRecord],
    ) -> tuple[list[InferredRelationship], list[InferredRelationship], list[RelationshipValidationDebugRecord]]:
        entity_map = {entity.id: entity for entity in entities}
        intent_map: dict[tuple[str, str], list[NormalizedIntentRecord]] = {}
        for intent in intents:
            if intent.source_tag and intent.target_tag:
                intent_map.setdefault((intent.source_tag, intent.target_tag), []).append(intent)

        validated: list[InferredRelationship] = []
        rejected: list[InferredRelationship] = []
        debug_records: list[RelationshipValidationDebugRecord] = []

        for candidate in candidates:
            related_intents = intent_map.get((candidate.source_entity, candidate.target_entity), [])
            intent_type = related_intents[0].intent_type if related_intents else self._infer_intent_type(entity_map.get(candidate.source_entity))
            text_support = self._relationship_text_support(candidate, related_intents)
            topology_support = self._relationship_topology_support(candidate, entity_map)
            naming_support = self._relationship_naming_support(candidate, intent_type)
            support_count = sum(1 for item in (text_support, topology_support, naming_support) if item.supported)
            rejection_reasons = self._rejection_reasons(text_support, topology_support, naming_support, support_count)
            boosted_confidence = min(0.99, candidate.confidence_score + (0.06 * max(0, support_count - 1)))

            updated = candidate.model_copy(
                update={
                    "confidence_score": boosted_confidence,
                    "confidence_level": "HIGH" if boosted_confidence >= 0.85 else "MEDIUM" if boosted_confidence >= 0.6 else "LOW",
                    "explanation": self._relationship_explanation(candidate.explanation, text_support, topology_support, naming_support, support_count, rejection_reasons),
                }
            )
            debug_records.append(
                RelationshipValidationDebugRecord(
                    candidate_id=f"relationship:{candidate.source_entity}:{candidate.relationship_type}:{candidate.target_entity}",
                    source_tag=candidate.source_entity,
                    target_tag=candidate.target_entity,
                    relationship_type=candidate.relationship_type,
                    text_support=text_support,
                    topology_support=topology_support,
                    naming_support=naming_support,
                    support_count=support_count,
                    validated=support_count >= 2,
                    rejection_reasons=rejection_reasons,
                )
            )

            if support_count >= 2:
                validated.append(updated)
            else:
                rejected.append(updated)
                self.logger.debug(
                    "relationship_rejected source=%s target=%s type=%s support_count=%s reasons=%s",
                    candidate.source_entity,
                    candidate.target_entity,
                    candidate.relationship_type,
                    support_count,
                    rejection_reasons,
                )

        return validated, rejected, sorted(debug_records, key=lambda item: (item.source_tag, item.target_tag, item.relationship_type))

    def validate_loops(
        self,
        candidates: list[PipelineControlLoopRecord],
        entities: list[EngineeringEntity],
    ) -> tuple[list[PipelineControlLoopRecord], list[PipelineControlLoopRecord], list[LoopValidationDebugRecord]]:
        entity_map = {entity.id: entity for entity in entities}
        validated: list[PipelineControlLoopRecord] = []
        rejected: list[PipelineControlLoopRecord] = []
        debug_records: list[LoopValidationDebugRecord] = []

        for candidate in candidates:
            text_support = ValidationSignalRecord(
                supported=bool(candidate.source_texts),
                evidence=sorted({text[:180] for text in candidate.source_texts if text})[:4],
            )
            topology_support = self._loop_topology_support(candidate, entity_map)
            naming_support = self._loop_naming_support(candidate)
            support_count = sum(1 for item in (text_support, topology_support, naming_support) if item.supported)
            rejection_reasons = self._rejection_reasons(text_support, topology_support, naming_support, support_count)
            validation_score = self._loop_validation_score(text_support, topology_support, naming_support)
            overall_confidence = self._combine_loop_confidence(
                completeness_score=float(candidate.completeness_score or 0.0),
                continuity_score=float(candidate.continuity_score or 0.0),
                validation_score=validation_score,
                relationship_score=float(candidate.relationship_score or 0.0),
            )

            updated = candidate.model_copy(
                update={
                    "support": self._loop_support_labels(text_support, topology_support, naming_support),
                    "support_count": support_count,
                    "validation_score": validation_score,
                    "confidence": overall_confidence,
                }
            )
            debug_records.append(
                LoopValidationDebugRecord(
                    candidate_id=candidate.loop_id,
                    sensor_tag=candidate.sensor_tag,
                    actuator_tag=candidate.actuator_tag,
                    process_node=candidate.process_node,
                    intent_type=candidate.intent_type,
                    text_support=text_support,
                    topology_support=topology_support,
                    naming_support=naming_support,
                    support_count=support_count,
                    validated=support_count >= 2,
                    visible_by_default=True,
                    visibility_threshold=0.0,
                    rejection_reasons=rejection_reasons,
                )
            )

            if support_count >= 2:
                validated.append(updated)
            else:
                rejected.append(updated)
                self.logger.debug(
                    "loop_rejected sensor=%s actuator=%s process=%s support_count=%s reasons=%s",
                    candidate.sensor_tag,
                    candidate.actuator_tag,
                    candidate.process_node,
                    support_count,
                    rejection_reasons,
                )

        return validated, rejected, sorted(debug_records, key=lambda item: (item.process_node, item.sensor_tag, item.actuator_tag))

    @staticmethod
    def _loop_validation_score(
        text_support: ValidationSignalRecord,
        topology_support: ValidationSignalRecord,
        naming_support: ValidationSignalRecord,
    ) -> float:
        return round(
            min(
                1.0,
                0.2
                + (0.35 if topology_support.supported else 0.0)
                + (0.25 if text_support.supported else 0.0)
                + (0.2 if naming_support.supported else 0.0),
            ),
            3,
        )

    @staticmethod
    def _combine_loop_confidence(
        *,
        completeness_score: float,
        continuity_score: float,
        validation_score: float,
        relationship_score: float,
    ) -> float:
        return round(
            max(
                0.0,
                min(
                    0.99,
                    (0.24 * completeness_score)
                    + (0.28 * continuity_score)
                    + (0.24 * validation_score)
                    + (0.24 * relationship_score),
                ),
            ),
            3,
        )

    @staticmethod
    def _relationship_text_support(candidate: InferredRelationship, intents: list[NormalizedIntentRecord]) -> ValidationSignalRecord:
        evidence = sorted({ref for ref in candidate.source_references if ref})
        intent_refs = sorted({intent.source_section_reference for intent in intents if intent.source_section_reference})
        for item in intent_refs:
            if item not in evidence:
                evidence.append(item)
        return ValidationSignalRecord(supported=bool(evidence), evidence=evidence[:4])

    @staticmethod
    def _relationship_topology_support(candidate: InferredRelationship, entity_map: dict[str, EngineeringEntity]) -> ValidationSignalRecord:
        source = entity_map.get(candidate.source_entity)
        target = entity_map.get(candidate.target_entity)
        evidence: list[str] = []
        supported = False
        if source and target and source.process_unit and target.process_unit and source.process_unit == target.process_unit:
            supported = True
            evidence.append(f"same_process_unit:{source.process_unit}")
        if source and target and candidate.relationship_type == "MEASURES" and target.canonical_type == "process_unit":
            supported = True
            evidence.append(f"measures_process_unit:{target.id}")
        if candidate.relationship_type == "PART_OF":
            supported = True
            evidence.append("structural_part_of")
        return ValidationSignalRecord(supported=supported, evidence=evidence)

    def _relationship_naming_support(self, candidate: InferredRelationship, intent_type: str | None) -> ValidationSignalRecord:
        evidence: list[str] = []
        source_digits = "".join(re.findall(r"\d+", candidate.source_entity))
        target_digits = "".join(re.findall(r"\d+", candidate.target_entity))
        supported = False
        if source_digits and target_digits and source_digits == target_digits:
            supported = True
            evidence.append(f"shared_digits:{source_digits}")
        if intent_type and self._tag_pattern_support(candidate.source_entity, candidate.target_entity, intent_type):
            supported = True
            evidence.append(f"intent_pattern:{intent_type}")
        return ValidationSignalRecord(supported=supported, evidence=evidence)

    @staticmethod
    def _loop_topology_support(candidate: PipelineControlLoopRecord, entity_map: dict[str, EngineeringEntity]) -> ValidationSignalRecord:
        sensor = entity_map.get(candidate.sensor_tag)
        actuator = entity_map.get(candidate.actuator_tag)
        evidence: list[str] = []
        supported = False
        if sensor and actuator and sensor.process_unit and actuator.process_unit and sensor.process_unit == actuator.process_unit:
            supported = True
            evidence.append(f"shared_process_unit:{sensor.process_unit}")
        if candidate.process_node:
            if sensor and sensor.process_unit == candidate.process_node:
                supported = True
                evidence.append(f"sensor_process:{candidate.process_node}")
            if actuator and actuator.process_unit == candidate.process_node:
                supported = True
                evidence.append(f"actuator_process:{candidate.process_node}")
        return ValidationSignalRecord(supported=supported, evidence=evidence)

    def _loop_naming_support(self, candidate: PipelineControlLoopRecord) -> ValidationSignalRecord:
        evidence: list[str] = []
        supported = False
        source_digits = "".join(re.findall(r"\d+", candidate.sensor_tag))
        target_digits = "".join(re.findall(r"\d+", candidate.actuator_tag))
        if source_digits and target_digits and source_digits == target_digits:
            supported = True
            evidence.append(f"shared_digits:{source_digits}")
        if candidate.intent_type and self._tag_pattern_support(candidate.sensor_tag, candidate.actuator_tag, candidate.intent_type):
            supported = True
            evidence.append(f"intent_pattern:{candidate.intent_type}")
        return ValidationSignalRecord(supported=supported, evidence=evidence)

    @staticmethod
    def _rejection_reasons(
        text_support: ValidationSignalRecord,
        topology_support: ValidationSignalRecord,
        naming_support: ValidationSignalRecord,
        support_count: int,
    ) -> list[str]:
        reasons: list[str] = []
        if not text_support.supported:
            reasons.append("missing_document_text_support")
        if not topology_support.supported:
            reasons.append("missing_graph_topology_support")
        if not naming_support.supported:
            reasons.append("missing_tag_naming_support")
        if support_count < 2:
            reasons.append("support_count_below_threshold")
        return reasons

    @staticmethod
    def _relationship_explanation(
        base: str,
        text_support: ValidationSignalRecord,
        topology_support: ValidationSignalRecord,
        naming_support: ValidationSignalRecord,
        support_count: int,
        rejection_reasons: list[str],
    ) -> str:
        details = [
            f"text={text_support.supported}:{';'.join(text_support.evidence) or 'none'}",
            f"topology={topology_support.supported}:{';'.join(topology_support.evidence) or 'none'}",
            f"naming={naming_support.supported}:{';'.join(naming_support.evidence) or 'none'}",
            f"support_count={support_count}",
        ]
        if rejection_reasons:
            details.append(f"rejection_reasons={','.join(rejection_reasons)}")
        return f"{base} Cross-validation: {' | '.join(details)}."

    @staticmethod
    def _loop_support_labels(
        text_support: ValidationSignalRecord,
        topology_support: ValidationSignalRecord,
        naming_support: ValidationSignalRecord,
    ) -> list[str]:
        labels: list[str] = []
        if text_support.supported:
            labels.append("document_text")
        if topology_support.supported:
            labels.append("graph_topology")
        if naming_support.supported:
            labels.append("tag_naming_pattern")
        return labels

    @staticmethod
    def _infer_intent_type(entity: EngineeringEntity | None) -> str | None:
        if entity is None:
            return None
        mapping = {
            "flow_transmitter": "flow_control",
            "level_transmitter": "level_control",
            "level_switch": "level_control",
            "pressure_transmitter": "pressure_control",
            "differential_pressure_transmitter": "pressure_control",
            "temperature_transmitter": "temperature_control",
        }
        return mapping.get(entity.canonical_type)

    @staticmethod
    def _tag_pattern_support(source_tag: str, target_tag: str, intent_type: str | None) -> bool:
        if not source_tag or not target_tag or intent_type is None:
            return False
        source_digits = "".join(re.findall(r"\d+", source_tag))
        target_digits = "".join(re.findall(r"\d+", target_tag))
        if source_digits and target_digits and source_digits == target_digits:
            return True
        expected_pairs = {
            "flow_control": ("F", "FCV"),
            "level_control": ("L", "P"),
            "pressure_control": ("P", "V"),
            "temperature_control": ("T", "V"),
        }
        expected = expected_pairs.get(intent_type)
        if expected is None:
            return False
        return source_tag.split("-")[0].startswith(expected[0]) and target_tag.split("-")[0].startswith(expected[1])


cross_validation_service = CrossValidationService()