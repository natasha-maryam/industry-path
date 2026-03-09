from __future__ import annotations

import logging

from models.pipeline import EngineeringEntity, InferredRelationship, ProcessUnit


class ProcessUnitAssignmentService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _best_unit_for_entity(entity: EngineeringEntity, units: list[ProcessUnit]) -> str | None:
        unit_ids = {unit.id: unit for unit in units}

        if entity.canonical_type == "blower" and "BLOWER-PACKAGE" in unit_ids:
            return "BLOWER-PACKAGE"
        if entity.canonical_type in {"analyzer", "control_valve"} and "AERATION-BASIN-AREA" in unit_ids:
            return "AERATION-BASIN-AREA"
        if entity.canonical_type == "pump" and "INFLUENT-PUMP-STATION" in unit_ids:
            return "INFLUENT-PUMP-STATION"
        if entity.id.startswith("CL-") and "CLARIFIER-AREA" in unit_ids:
            return "CLARIFIER-AREA"
        if entity.id.startswith("BAS-") and "AERATION-BASIN-AREA" in unit_ids:
            return "AERATION-BASIN-AREA"
        if entity.canonical_type in {"flow_transmitter", "level_transmitter", "level_switch"}:
            if "INFLUENT-PUMP-STATION" in unit_ids:
                return "INFLUENT-PUMP-STATION"
            if "AERATION-BASIN-AREA" in unit_ids:
                return "AERATION-BASIN-AREA"

        # fallback by confidence rank
        if units:
            return sorted(units, key=lambda item: item.confidence, reverse=True)[0].id
        return None

    def assign(
        self,
        entities: list[EngineeringEntity],
        process_units: list[ProcessUnit],
    ) -> tuple[list[EngineeringEntity], list[InferredRelationship], list[str]]:
        relationships: list[InferredRelationship] = []
        warnings: list[str] = []

        for entity in entities:
            if entity.is_synthetic:
                continue
            assigned = self._best_unit_for_entity(entity, process_units)
            if assigned is None:
                warnings.append(f"{entity.id} classified but no reliable process_unit assignment")
                continue
            entity.process_unit = assigned
            relationships.append(
                InferredRelationship(
                    relationship_type="PART_OF",
                    source_entity=entity.id,
                    target_entity=assigned,
                    confidence_score=0.84,
                    confidence_level="HIGH",
                    inference_source="assignment",
                    explanation=f"Device assigned to {assigned} by deterministic process-unit rules.",
                    source_references=["process_unit_assignment"],
                )
            )

        self.logger.info("Process unit assignment: part_of_edges=%s warnings=%s", len(relationships), len(warnings))
        return entities, relationships, warnings


process_unit_assignment_service = ProcessUnitAssignmentService()
