from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass

from models.document_pipeline import NormalizedIntentRecord, PipelineControlLoopRecord
from models.pipeline import EngineeringEntity, InferredRelationship
from services.signal_classification import classify_behavioral_role


@dataclass(frozen=True)
class _RoleAssignment:
    role: str
    evidence: tuple[str, ...]
    confidence: float


class StrictDeterministicControlLoopEngine:
    CONTROL_EDGE_TYPES = {"CONTROLS", "SIGNAL_TO", "SUPPORTS"}
    PROCESS_EDGE_TYPES = {"PART_OF", "PROCESS_FLOW", "FEEDS", "DISCHARGES_TO", "CONNECTED_TO", "SUPPLIES_AIR_TO", "CONTROLS"}
    MEASUREMENT_EDGE_TYPES = {"MEASURES", "MONITORS"}

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def discover(
        self,
        *,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
        metadata_by_entity: dict[str, dict[str, object]] | None = None,
        intents: list[NormalizedIntentRecord] | None = None,
    ) -> tuple[list[PipelineControlLoopRecord], list[str]]:
        metadata = metadata_by_entity or {}
        normalized_intents = intents or []
        entity_map = {entity.id: entity for entity in entities}
        role_map = self._role_map(entities, metadata)
        outgoing = self._outgoing_relationships(relationships)
        measured_processes = self._measured_processes(relationships, role_map)
        loops: dict[tuple[str, str, str], PipelineControlLoopRecord] = {}
        warnings: list[str] = []

        for sensor_id, assignment in sorted(role_map.items()):
            if assignment.role != "sensor":
                continue

            explicit_paths = self._explicit_controller_paths(sensor_id, outgoing, role_map)
            direct_paths = self._direct_actuator_paths(sensor_id, outgoing, role_map)

            for controller_id, actuator_id, process_id, chain_edges in explicit_paths:
                invalid_reasons = self._validate_chain(
                    sensor_id=sensor_id,
                    controller_id=controller_id,
                    actuator_id=actuator_id,
                    process_id=process_id,
                    outgoing=outgoing,
                    measured_processes=measured_processes,
                )
                if invalid_reasons:
                    warnings.append(self._rejection_message(sensor_id, controller_id, actuator_id, process_id, invalid_reasons))
                    continue

                loop = self._build_loop_record(
                    sensor_id=sensor_id,
                    controller_id=controller_id,
                    actuator_id=actuator_id,
                    process_id=process_id,
                    role_map=role_map,
                    relationship_chain=chain_edges,
                    intents=normalized_intents,
                    controller_inferred=False,
                )
                self._deduplicate_loop(loops, loop)

            for actuator_id, process_id, chain_edges in direct_paths:
                inferred_controller = self._infer_controller_tag(sensor_id, actuator_id, process_id)
                invalid_reasons = self._validate_chain(
                    sensor_id=sensor_id,
                    controller_id=inferred_controller,
                    actuator_id=actuator_id,
                    process_id=process_id,
                    outgoing=outgoing,
                    measured_processes=measured_processes,
                    inferred_controller=True,
                )
                if invalid_reasons:
                    warnings.append(self._rejection_message(sensor_id, inferred_controller, actuator_id, process_id, invalid_reasons))
                    continue

                loop = self._build_loop_record(
                    sensor_id=sensor_id,
                    controller_id=inferred_controller,
                    actuator_id=actuator_id,
                    process_id=process_id,
                    role_map=role_map,
                    relationship_chain=chain_edges,
                    intents=normalized_intents,
                    controller_inferred=True,
                )
                self._deduplicate_loop(loops, loop)

        ordered = sorted(loops.values(), key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node))
        self.logger.info("Strict control loop engine: discovered=%s warnings=%s", len(ordered), len(warnings))
        return ordered, warnings

    @staticmethod
    def _deduplicate_loop(
        loops: dict[tuple[str, str, str], PipelineControlLoopRecord],
        loop: PipelineControlLoopRecord,
    ) -> None:
        key = (loop.sensor_tag, loop.actuator_tag, loop.process_node)
        existing = loops.get(key)
        if existing is None:
            loops[key] = loop
            return
        replacement_rank = (loop.confidence, loop.validation_score, loop.continuity_score, bool(loop.controller_tag and not str(loop.controller_tag).startswith("CTRL_")))
        existing_rank = (existing.confidence, existing.validation_score, existing.continuity_score, bool(existing.controller_tag and not str(existing.controller_tag).startswith("CTRL_")))
        if replacement_rank > existing_rank:
            loops[key] = loop

    def _role_map(
        self,
        entities: list[EngineeringEntity],
        metadata_by_entity: dict[str, dict[str, object]],
    ) -> dict[str, _RoleAssignment]:
        assignments: dict[str, _RoleAssignment] = {}
        for entity in entities:
            metadata = metadata_by_entity.get(entity.id, {})
            role, evidence, confidence = classify_behavioral_role(
                entity.id,
                node_type=entity.canonical_type,
                normalized_equipment=str(metadata.get("equipment_type") or metadata.get("normalized_equipment") or ""),
                normalized_type=str(metadata.get("normalized_type") or entity.canonical_type),
            )
            assignments[entity.id] = _RoleAssignment(role=role, evidence=tuple(sorted(set(evidence))), confidence=confidence)
        return assignments

    @staticmethod
    def _outgoing_relationships(relationships: list[InferredRelationship]) -> dict[str, list[InferredRelationship]]:
        outgoing: dict[str, list[InferredRelationship]] = defaultdict(list)
        for relationship in relationships:
            outgoing[relationship.source_entity].append(relationship)
        return outgoing

    def _measured_processes(
        self,
        relationships: list[InferredRelationship],
        role_map: dict[str, _RoleAssignment],
    ) -> dict[str, set[str]]:
        measured: dict[str, set[str]] = defaultdict(set)
        for relationship in relationships:
            if relationship.relationship_type not in self.MEASUREMENT_EDGE_TYPES:
                continue
            if role_map.get(relationship.source_entity, _RoleAssignment("equipment", (), 0.0)).role != "sensor":
                continue
            if role_map.get(relationship.target_entity, _RoleAssignment("equipment", (), 0.0)).role != "process":
                continue
            measured[relationship.source_entity].add(relationship.target_entity)
        return measured

    def _explicit_controller_paths(
        self,
        sensor_id: str,
        outgoing: dict[str, list[InferredRelationship]],
        role_map: dict[str, _RoleAssignment],
    ) -> list[tuple[str, str, str, list[InferredRelationship]]]:
        discovered: list[tuple[str, str, str, list[InferredRelationship]]] = []
        for first_edge in outgoing.get(sensor_id, []):
            if first_edge.relationship_type not in self.CONTROL_EDGE_TYPES:
                continue
            controller_id = first_edge.target_entity
            if role_map.get(controller_id, _RoleAssignment("equipment", (), 0.0)).role != "controller":
                continue
            for second_edge in outgoing.get(controller_id, []):
                if second_edge.relationship_type not in self.CONTROL_EDGE_TYPES:
                    continue
                actuator_id = second_edge.target_entity
                if role_map.get(actuator_id, _RoleAssignment("equipment", (), 0.0)).role != "actuator":
                    continue
                for third_edge in outgoing.get(actuator_id, []):
                    if third_edge.relationship_type not in self.PROCESS_EDGE_TYPES:
                        continue
                    process_id = third_edge.target_entity
                    if role_map.get(process_id, _RoleAssignment("equipment", (), 0.0)).role != "process":
                        continue
                    discovered.append((controller_id, actuator_id, process_id, [first_edge, second_edge, third_edge]))
        return discovered

    def _direct_actuator_paths(
        self,
        sensor_id: str,
        outgoing: dict[str, list[InferredRelationship]],
        role_map: dict[str, _RoleAssignment],
    ) -> list[tuple[str, str, list[InferredRelationship]]]:
        discovered: list[tuple[str, str, list[InferredRelationship]]] = []
        for first_edge in outgoing.get(sensor_id, []):
            if first_edge.relationship_type not in self.CONTROL_EDGE_TYPES:
                continue
            actuator_id = first_edge.target_entity
            if role_map.get(actuator_id, _RoleAssignment("equipment", (), 0.0)).role != "actuator":
                continue
            for second_edge in outgoing.get(actuator_id, []):
                if second_edge.relationship_type not in self.PROCESS_EDGE_TYPES:
                    continue
                process_id = second_edge.target_entity
                if role_map.get(process_id, _RoleAssignment("equipment", (), 0.0)).role != "process":
                    continue
                discovered.append((actuator_id, process_id, [first_edge, second_edge]))
        return discovered

    def _validate_chain(
        self,
        *,
        sensor_id: str,
        controller_id: str,
        actuator_id: str,
        process_id: str,
        outgoing: dict[str, list[InferredRelationship]],
        measured_processes: dict[str, set[str]],
        inferred_controller: bool = False,
    ) -> list[str]:
        reasons: list[str] = []
        if not sensor_id or not actuator_id or not process_id:
            reasons.append("missing_required_roles")

        required_nodes = [sensor_id, actuator_id, process_id]
        if not inferred_controller:
            required_nodes.insert(1, controller_id)
        if len(set(required_nodes)) != len(required_nodes):
            reasons.append("repeated_nodes_in_chain")

        if inferred_controller:
            if not self._has_direct_edge(outgoing, sensor_id, actuator_id, self.CONTROL_EDGE_TYPES):
                reasons.append("missing_sensor_to_actuator_downstream_edge")
        else:
            if not controller_id:
                reasons.append("missing_controller_role")
            elif not self._has_direct_edge(outgoing, sensor_id, controller_id, self.CONTROL_EDGE_TYPES):
                reasons.append("missing_sensor_to_controller_downstream_edge")
            elif not self._has_direct_edge(outgoing, controller_id, actuator_id, self.CONTROL_EDGE_TYPES):
                reasons.append("missing_controller_to_actuator_downstream_edge")

        if not self._has_direct_edge(outgoing, actuator_id, process_id, self.PROCESS_EDGE_TYPES):
            reasons.append("missing_actuator_to_process_downstream_edge")

        measured = measured_processes.get(sensor_id, set())
        if process_id not in measured:
            reasons.append("sensor_not_linked_to_process")

        return reasons

    @staticmethod
    def _has_direct_edge(
        outgoing: dict[str, list[InferredRelationship]],
        source_id: str,
        target_id: str,
        accepted_types: set[str],
    ) -> bool:
        return any(
            relationship.target_entity == target_id and relationship.relationship_type in accepted_types
            for relationship in outgoing.get(source_id, [])
        )

    def _build_loop_record(
        self,
        *,
        sensor_id: str,
        controller_id: str,
        actuator_id: str,
        process_id: str,
        role_map: dict[str, _RoleAssignment],
        relationship_chain: list[InferredRelationship],
        intents: list[NormalizedIntentRecord],
        controller_inferred: bool,
    ) -> PipelineControlLoopRecord:
        related_texts = self._related_source_texts(sensor_id, controller_id, actuator_id, intents)
        evidence = [reference for relationship in relationship_chain for reference in relationship.source_references if reference]
        chain = [sensor_id, controller_id, actuator_id, process_id]
        completeness_score = 1.0 if not controller_inferred else 0.88
        continuity_score = 1.0 if not controller_inferred else 0.9
        validation_score = self._initial_validation_score(sensor_id, controller_id, actuator_id, related_texts, evidence)
        relationship_score = round(sum(relationship.confidence_score for relationship in relationship_chain) / max(len(relationship_chain), 1), 3)
        confidence = self._combined_confidence(
            completeness_score=completeness_score,
            continuity_score=continuity_score,
            validation_score=validation_score,
            relationship_score=relationship_score,
        )
        tuning_confidence = min(0.85, 0.55 if not controller_inferred else 0.42)

        return PipelineControlLoopRecord(
            loop_id=f"loop:{sensor_id}:{controller_id}:{actuator_id}:{process_id}",
            name=f"{sensor_id} -> {controller_id} -> {actuator_id} -> {process_id}",
            sensor_tag=sensor_id,
            controller_tag=controller_id,
            actuator_tag=actuator_id,
            process_node=process_id,
            chain=chain,
            intent_type=self._infer_intent_type(sensor_id, actuator_id, intents),
            source_texts=sorted(set([*related_texts, *evidence]))[:6],
            support=["graph_topology"],
            support_count=1,
            completeness_score=round(completeness_score, 3),
            continuity_score=round(continuity_score, 3),
            validation_score=round(validation_score, 3),
            relationship_score=round(relationship_score, 3),
            confidence=round(confidence, 3),
            tuning_confidence=round(tuning_confidence, 3),
        )

    def _initial_validation_score(
        self,
        sensor_id: str,
        controller_id: str,
        actuator_id: str,
        related_texts: list[str],
        evidence: list[str],
    ) -> float:
        source_signals = 0
        if related_texts:
            source_signals += 1
        if evidence:
            source_signals += 1
        if self._shared_digits(sensor_id, actuator_id) or self._shared_digits(sensor_id, controller_id):
            source_signals += 1
        return min(1.0, max(0.34, source_signals / 3.0))

    @staticmethod
    def _combined_confidence(
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
    def _related_source_texts(
        sensor_id: str,
        controller_id: str,
        actuator_id: str,
        intents: list[NormalizedIntentRecord],
    ) -> list[str]:
        texts: list[str] = []
        for intent in intents:
            if intent.source_tag != sensor_id:
                continue
            if intent.target_tag in {controller_id, actuator_id} and intent.source_text:
                texts.append(intent.source_text[:220])
        return sorted(set(texts))

    @staticmethod
    def _infer_intent_type(sensor_id: str, actuator_id: str, intents: list[NormalizedIntentRecord]) -> str | None:
        for intent in intents:
            if intent.source_tag == sensor_id and intent.target_tag in {actuator_id}:
                return intent.intent_type
        return None

    @staticmethod
    def _infer_controller_tag(sensor_id: str, actuator_id: str, process_id: str) -> str:
        shared_digits = StrictDeterministicControlLoopEngine._shared_digits(sensor_id, actuator_id)
        suffix = shared_digits or re.sub(r"[^A-Za-z0-9]+", "_", process_id).strip("_").upper() or "GENERIC"
        return f"CTRL_{suffix}"

    @staticmethod
    def _shared_digits(left: str, right: str) -> str:
        left_digits = "".join(re.findall(r"\d+", left))
        right_digits = "".join(re.findall(r"\d+", right))
        return left_digits if left_digits and left_digits == right_digits else ""

    @staticmethod
    def _rejection_message(
        sensor_id: str,
        controller_id: str,
        actuator_id: str,
        process_id: str,
        reasons: list[str],
    ) -> str:
        return (
            f"Rejected deterministic loop path {sensor_id} -> {controller_id} -> {actuator_id} -> {process_id}: "
            f"{','.join(sorted(set(reasons)))}"
        )


strict_control_loop_engine = StrictDeterministicControlLoopEngine()