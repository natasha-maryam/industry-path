from __future__ import annotations

import logging
from collections import defaultdict

from models.pipeline import EngineeringEntity, InferredRelationship


class RelationshipInferenceService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def infer(
        self,
        entities: list[EngineeringEntity],
        rule_bundle: dict[str, list],
        pid_chunks,
    ) -> tuple[list[InferredRelationship], list[InferredRelationship], list[str]]:
        high_medium: list[InferredRelationship] = []
        low_confidence: list[InferredRelationship] = []
        warnings: list[str] = []

        entity_map = {entity.id: entity for entity in entities}
        relationships = self._narrative_relationships(entity_map, rule_bundle)
        relationships.extend(self._heuristic_relationships(entities))
        relationships.extend(self._locality_support_relationships(entities, pid_chunks))

        dedup: dict[tuple[str, str, str], InferredRelationship] = {}
        for rel in relationships:
            key = (rel.source_entity, rel.target_entity, rel.relationship_type)
            existing = dedup.get(key)
            if existing is None or rel.confidence_score > existing.confidence_score:
                dedup[key] = rel

        for rel in dedup.values():
            if rel.confidence_level == "LOW":
                low_confidence.append(rel)
            else:
                high_medium.append(rel)

        if not high_medium:
            warnings.append("No HIGH/MEDIUM engineering relationships inferred from current documents.")

        self.logger.info(
            "Relationship inference: high_medium=%s low=%s",
            len(high_medium),
            len(low_confidence),
        )
        return high_medium, low_confidence, warnings

    def _narrative_relationships(self, entity_map: dict[str, EngineeringEntity], rule_bundle: dict[str, list]) -> list[InferredRelationship]:
        results: list[InferredRelationship] = []

        for loop in rule_bundle.get("control_loops", []):
            tags = [tag for tag in loop.related_tags if tag in entity_map]
            if len(tags) < 2:
                continue
            for source in tags:
                for target in tags:
                    if source == target:
                        continue
                    source_entity = entity_map[source]
                    target_entity = entity_map[target]
                    if source_entity.canonical_type in {"analyzer", "flow_transmitter", "level_transmitter", "pressure_transmitter"} and target_entity.canonical_type in {"control_valve", "valve", "pump", "blower"}:
                        results.append(
                            InferredRelationship(
                                relationship_type="CONTROLS",
                                source_entity=source,
                                target_entity=target,
                                confidence_score=0.92,
                                confidence_level="HIGH",
                                inference_source="narrative",
                                explanation=f"Narrative control loop suggests {source} influences {target}.",
                                source_references=[loop.source_sentence],
                            )
                        )

        for alarm in rule_bundle.get("alarms", []):
            tags = [tag for tag in alarm.related_tags if tag in entity_map]
            if not tags:
                continue
            for tag in tags:
                results.append(
                    InferredRelationship(
                        relationship_type="ALARMS_ON",
                        source_entity=tag,
                        target_entity=tag,
                        confidence_score=0.82,
                        confidence_level="HIGH",
                        inference_source="narrative",
                        explanation=f"Alarm text references {tag}.",
                        source_references=[alarm.source_sentence],
                    )
                )

        for interlock in rule_bundle.get("interlocks", []):
            tags = [tag for tag in interlock.related_tags if tag in entity_map]
            if len(tags) < 2:
                continue
            source = tags[0]
            for target in tags[1:]:
                if source == target:
                    continue
                results.append(
                    InferredRelationship(
                        relationship_type="INTERLOCKS_WITH",
                        source_entity=source,
                        target_entity=target,
                        confidence_score=0.88,
                        confidence_level="HIGH",
                        inference_source="narrative",
                        explanation=f"Interlock/permissive statement links {source} and {target}.",
                        source_references=[interlock.source_sentence],
                    )
                )

        return results

    def _heuristic_relationships(self, entities: list[EngineeringEntity]) -> list[InferredRelationship]:
        results: list[InferredRelationship] = []
        by_unit: dict[str, list[EngineeringEntity]] = defaultdict(list)
        for entity in entities:
            by_unit[entity.process_unit or "process_area_general"].append(entity)

        for unit, members in by_unit.items():
            pumps = [entity for entity in members if entity.canonical_type == "pump"]
            level_instruments = [
                entity
                for entity in members
                if entity.canonical_type in {"level_transmitter", "level_switch"}
            ]
            analyzers = [entity for entity in members if entity.canonical_type == "analyzer"]
            control_valves = [entity for entity in members if entity.canonical_type == "control_valve"]
            blowers = [entity for entity in members if entity.canonical_type == "blower"]

            for instrument in level_instruments:
                for pump in pumps:
                    results.append(
                        InferredRelationship(
                            relationship_type="SIGNAL_TO",
                            source_entity=instrument.id,
                            target_entity=pump.id,
                            confidence_score=0.74,
                            confidence_level="MEDIUM",
                            inference_source="heuristic",
                            explanation=f"Level instrumentation commonly stages pumps in {unit}.",
                            source_references=[f"process_unit:{unit}"],
                        )
                    )

            for analyzer in analyzers:
                for valve in control_valves:
                    results.append(
                        InferredRelationship(
                            relationship_type="CONTROLS",
                            source_entity=analyzer.id,
                            target_entity=valve.id,
                            confidence_score=0.78,
                            confidence_level="MEDIUM",
                            inference_source="heuristic",
                            explanation=f"Analyzer and control valve grouped in {unit}.",
                            source_references=[f"process_unit:{unit}"],
                        )
                    )

            for blower in blowers:
                support_targets = [
                    entity
                    for entity in members
                    if entity.id != blower.id and entity.canonical_type in {"control_valve", "analyzer", "flow_transmitter", "generic_device", "tank"}
                ]
                for target in support_targets[:2]:
                    results.append(
                        InferredRelationship(
                            relationship_type="SUPPORTS",
                            source_entity=blower.id,
                            target_entity=target.id,
                            confidence_score=0.71,
                            confidence_level="MEDIUM",
                            inference_source="heuristic",
                            explanation="Blower supports nearby aeration/air-header control equipment.",
                            source_references=[f"process_unit:{unit}"],
                        )
                    )

        return results

    def _locality_support_relationships(self, entities: list[EngineeringEntity], pid_chunks) -> list[InferredRelationship]:
        # Locality is secondary only: we emit low-confidence associated links for review.
        results: list[InferredRelationship] = []
        tag_to_pages: dict[str, set[int]] = {entity.id: set(entity.source_pages) for entity in entities}

        for source in entities:
            for target in entities:
                if source.id >= target.id:
                    continue
                if source.canonical_type in {"flow_transmitter", "level_transmitter", "pressure_transmitter", "analyzer"} and target.canonical_type in {"flow_transmitter", "level_transmitter", "pressure_transmitter", "analyzer"}:
                    continue
                shared_pages = tag_to_pages[source.id].intersection(tag_to_pages[target.id])
                if shared_pages:
                    results.append(
                        InferredRelationship(
                            relationship_type="ASSOCIATED_WITH",
                            source_entity=source.id,
                            target_entity=target.id,
                            confidence_score=0.42,
                            confidence_level="LOW",
                            inference_source="locality",
                            explanation="Same P&ID page; kept as suggestion only (not promoted).",
                            source_references=[f"pages:{sorted(shared_pages)}"],
                        )
                    )

        return results


relationship_inference_service = RelationshipInferenceService()
