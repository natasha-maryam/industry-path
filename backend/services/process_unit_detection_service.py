from __future__ import annotations

import logging

from models.pipeline import ProcessUnit, SyntheticNode


class ProcessUnitDetectionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def detect(self, pid_chunks, narrative_chunks, entities) -> tuple[list[ProcessUnit], list[SyntheticNode]]:
        text_blob = "\n".join([chunk.text.lower() for chunk in [*pid_chunks, *narrative_chunks]])
        units: list[ProcessUnit] = []
        synthetic_nodes: list[SyntheticNode] = []

        def add_unit(
            unit_id: str,
            name: str,
            canonical_type: str,
            aliases: list[str],
            refs: list[str],
            confidence: float,
        ) -> None:
            if any(unit.id == unit_id for unit in units):
                return
            units.append(
                ProcessUnit(
                    id=unit_id,
                    name=name,
                    canonical_type=canonical_type,
                    aliases=aliases,
                    source_references=refs,
                    confidence=confidence,
                )
            )

        if any(token in text_blob for token in ("influent", "wet well", "pump station")) or any(entity.canonical_type == "pump" for entity in entities):
            add_unit(
                "INFLUENT-PUMP-STATION",
                "Influent Pump Station",
                "pump_station",
                ["wet well", "pump station"],
                ["narrative/pid context"],
                0.84,
            )

        if any(token in text_blob for token in ("screen", "screening")):
            add_unit("SCREENING-UNIT-1", "Screening Unit", "screening_unit", ["screening"], ["narrative heading"], 0.8)

        if "grit" in text_blob:
            add_unit("GRIT-REMOVAL-1", "Grit Removal", "grit_unit", ["grit"], ["narrative heading"], 0.8)

        if any(token in text_blob for token in ("aeration", "dissolved oxygen", "do", "basin")) or any(entity.id.startswith("BAS-") for entity in entities):
            add_unit("AERATION-BASIN-AREA", "Aeration Basin Area", "aeration_basin", ["aeration"], ["narrative/pid context"], 0.9)

        if any(token in text_blob for token in ("clarifier",)) or any(entity.id.startswith("CL-") for entity in entities):
            add_unit("CLARIFIER-AREA", "Clarifier", "clarifier", ["clarifier"], ["narrative/pid context"], 0.86)

        if "sludge" in text_blob:
            add_unit("SLUDGE-HANDLING-AREA", "Sludge Handling", "sludge_handling", ["sludge"], ["narrative heading"], 0.78)

        if any(token in text_blob for token in ("chemical feed", "dosing", "ratio control")):
            add_unit("CHEMICAL-FEED-SKID", "Chemical Feed Skid", "chemical_feed", ["dosing"], ["narrative section"], 0.83)

        if any(entity.canonical_type == "blower" for entity in entities) or "blower" in text_blob:
            add_unit("BLOWER-PACKAGE", "Blower Package", "blower_package", ["air blower package"], ["narrative/pid context"], 0.88)

        if "air header" in text_blob or any(entity.canonical_type == "blower" for entity in entities):
            add_unit("AIR-HEADER-1", "Air Header", "air_header", ["air header"], ["narrative/pid context"], 0.81)
            synthetic_nodes.append(
                SyntheticNode(
                    id="AIR-HEADER-1",
                    label="AIR-HEADER-1",
                    process_unit="AERATION-BASIN-AREA",
                    confidence=0.81,
                    explanation="Synthetic process node inferred from blower/aeration context.",
                    source_references=["narrative: air header", "heuristic: blower presence"],
                )
            )

        if "wet well" in text_blob:
            synthetic_nodes.append(
                SyntheticNode(
                    id="WET-WELL-1",
                    label="WET-WELL-1",
                    process_unit="INFLUENT-PUMP-STATION",
                    confidence=0.79,
                    explanation="Synthetic process node inferred from wet-well mention.",
                    source_references=["narrative: wet well"],
                )
            )

        if any(entity.id.startswith("AIT-") for entity in entities) and any(entity.id.startswith("FCV-") for entity in entities):
            synthetic_nodes.append(
                SyntheticNode(
                    id="CONTROL-LOOP-DO-2301",
                    label="CONTROL-LOOP-DO-2301",
                    process_unit="AERATION-BASIN-AREA",
                    confidence=0.86,
                    explanation="Synthetic control loop node inferred from analyzer/air-valve narrative context.",
                    source_references=["narrative: dissolved oxygen control"],
                )
            )

        self.logger.info("Process unit detection: units=%s synthetic_nodes=%s", len(units), len(synthetic_nodes))
        return units, synthetic_nodes


process_unit_detection_service = ProcessUnitDetectionService()
