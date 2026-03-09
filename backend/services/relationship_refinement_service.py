from __future__ import annotations

import logging

from models.pipeline import EngineeringEntity, InferredRelationship, ProcessUnit


class RelationshipRefinementService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def refine(
        self,
        entities: list[EngineeringEntity],
        process_units: list[ProcessUnit],
        base_relationships: list[InferredRelationship],
        rule_bundle: dict[str, list],
    ) -> list[InferredRelationship]:
        refined: list[InferredRelationship] = list(base_relationships)
        entity_by_id = {entity.id: entity for entity in entities}
        unit_ids = {unit.id for unit in process_units}

        # Distinguish measurement from control/signal relationships.
        for entity in entities:
            if entity.canonical_type in {"analyzer", "flow_transmitter", "level_transmitter", "pressure_transmitter", "differential_pressure_transmitter"}:
                target = entity.process_unit or "PROCESS-UNKNOWN"
                if target in unit_ids:
                    refined.append(
                        InferredRelationship(
                            relationship_type="MEASURES",
                            source_entity=entity.id,
                            target_entity=target,
                            confidence_score=0.78,
                            confidence_level="MEDIUM",
                            inference_source="refinement",
                            explanation="Instrument measurement edge to assigned process unit.",
                            source_references=["type_rule:instrument->process_unit"],
                        )
                    )

        # Refine analyzer/control valve path to SIGNAL_TO, keep CONTROLS only when explicit.
        for relationship in list(refined):
            if relationship.relationship_type == "CONTROLS":
                source = entity_by_id.get(relationship.source_entity)
                target = entity_by_id.get(relationship.target_entity)
                if source and target and source.canonical_type in {"analyzer", "flow_transmitter", "level_transmitter", "pressure_transmitter"} and target.canonical_type in {"control_valve", "valve"}:
                    relationship.relationship_type = "SIGNAL_TO"
                    relationship.explanation = f"Signal edge refined from control edge: {relationship.explanation}"

        # Blower topology: blower -> air header -> aeration basin
        blower_ids = [entity.id for entity in entities if entity.canonical_type == "blower"]
        basin_ids = [entity.id for entity in entities if entity.id.startswith("BAS-") or entity.process_unit == "AERATION-BASIN-AREA"]
        air_header_id = next((entity.id for entity in entities if entity.id == "AIR-HEADER-1"), None)
        if air_header_id:
            for blower in blower_ids:
                refined.append(
                    InferredRelationship(
                        relationship_type="SUPPLIES_AIR_TO",
                        source_entity=blower,
                        target_entity=air_header_id,
                        confidence_score=0.86,
                        confidence_level="HIGH",
                        inference_source="refinement",
                        explanation="Blower supplies air header based on aeration/blower package context.",
                        source_references=["topology_rule:blower_air_header"],
                    )
                )
            for basin in basin_ids:
                if basin == air_header_id:
                    continue
                refined.append(
                    InferredRelationship(
                        relationship_type="FEEDS",
                        source_entity=air_header_id,
                        target_entity=basin,
                        confidence_score=0.8,
                        confidence_level="MEDIUM",
                        inference_source="refinement",
                        explanation="Air header feeds aeration basin cluster.",
                        source_references=["topology_rule:air_header_basin"],
                    )
                )

        # Pump flow direction towards downstream process areas when identifiable.
        for entity in entities:
            if entity.canonical_type != "pump":
                continue
            downstream = "SCREENING-UNIT-1" if "SCREENING-UNIT-1" in unit_ids else "GRIT-REMOVAL-1" if "GRIT-REMOVAL-1" in unit_ids else "AERATION-BASIN-AREA" if "AERATION-BASIN-AREA" in unit_ids else None
            if downstream:
                refined.append(
                    InferredRelationship(
                        relationship_type="FEEDS",
                        source_entity=entity.id,
                        target_entity=downstream,
                        confidence_score=0.74,
                        confidence_level="MEDIUM",
                        inference_source="refinement",
                        explanation="Pump flow direction inferred from process unit chain.",
                        source_references=["topology_rule:pump_downstream"],
                    )
                )

        # Level switches should alarm/interlock pumps rather than generic controls.
        pumps = [entity.id for entity in entities if entity.canonical_type == "pump"]
        for entity in entities:
            if entity.canonical_type != "level_switch":
                continue
            for pump in pumps[:2]:
                refined.append(
                    InferredRelationship(
                        relationship_type="INTERLOCKS_WITH",
                        source_entity=entity.id,
                        target_entity=pump,
                        confidence_score=0.77,
                        confidence_level="MEDIUM",
                        inference_source="refinement",
                        explanation="Level switch likely interlocks pump staging/trip logic.",
                        source_references=["type_rule:level_switch_pump_interlock"],
                    )
                )

        # Deduplicate strongest edges by key.
        dedup: dict[tuple[str, str, str], InferredRelationship] = {}
        for relationship in refined:
            key = (relationship.source_entity, relationship.target_entity, relationship.relationship_type)
            prior = dedup.get(key)
            if prior is None or relationship.confidence_score > prior.confidence_score:
                dedup[key] = relationship

        result = list(dedup.values())
        self.logger.info("Relationship refinement output edges=%s", len(result))
        return result


relationship_refinement_service = RelationshipRefinementService()
