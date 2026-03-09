from __future__ import annotations

import logging
from collections import defaultdict

from models.pipeline import DetectedTag, EngineeringEntity


class EntityClassificationService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def process_unit_hints() -> dict[str, tuple[str, ...]]:
        return {
            "influent_pump_station": ("influent", "wet well", "pump station"),
            "screening": ("screen", "screening"),
            "grit_removal": ("grit",),
            "aeration_basin": ("aeration", "do", "dissolved oxygen", "air header"),
            "clarifier": ("clarifier",),
            "sludge_handling": ("sludge",),
            "chemical_feed": ("chemical", "dosing", "feed ratio"),
            "blower_package": ("blower", "header pressure"),
        }

    def build_entities(self, detected_tags: list[DetectedTag]) -> list[EngineeringEntity]:
        grouped: dict[str, list[DetectedTag]] = defaultdict(list)
        for tag in detected_tags:
            grouped[tag.normalized_tag].append(tag)

        entities: list[EngineeringEntity] = []
        for normalized_tag, matches in grouped.items():
            first = matches[0]
            aliases = sorted({item.raw_tag.upper().replace(" ", "-").replace("_", "-") for item in matches})
            source_documents = sorted({item.source_file_name for item in matches})
            source_pages = sorted({item.source_page for item in matches})
            source_snippets = [item.source_text for item in matches[:5]]
            confidence = max(0.45, min(0.99, sum(item.confidence for item in matches) / len(matches)))

            entities.append(
                EngineeringEntity(
                    id=normalized_tag,
                    tag=normalized_tag,
                    canonical_type=first.canonical_type,
                    display_name=normalized_tag,
                    aliases=aliases,
                    source_documents=source_documents,
                    source_pages=source_pages,
                    source_snippets=source_snippets,
                    confidence=confidence,
                    parse_notes=[f"Detected {len(matches)} time(s) across uploaded documents"],
                )
            )

        self.logger.info("Entity classification produced %s entities", len(entities))
        return entities

    def assign_process_units(self, entities: list[EngineeringEntity], narrative_text: str) -> list[EngineeringEntity]:
        lowered = narrative_text.lower()
        hints = self.process_unit_hints()

        for entity in entities:
            assigned = None
            for unit_name, markers in hints.items():
                if any(marker in lowered for marker in markers):
                    if unit_name == "blower_package" and entity.canonical_type == "blower":
                        assigned = unit_name
                        break
                    if unit_name == "aeration_basin" and entity.canonical_type in {"analyzer", "control_valve", "blower"}:
                        assigned = unit_name
                        break
                    if unit_name == "influent_pump_station" and entity.canonical_type == "pump":
                        assigned = unit_name
                        break
                    if unit_name in {"chemical_feed", "screening", "grit_removal", "clarifier", "sludge_handling"}:
                        assigned = unit_name
                        break
            if assigned is None:
                if entity.canonical_type == "blower":
                    assigned = "blower_package"
                elif entity.canonical_type == "pump":
                    assigned = "influent_pump_station"
                elif entity.canonical_type in {"analyzer", "control_valve"}:
                    assigned = "aeration_basin"
                else:
                    assigned = "process_area_general"

            entity.process_unit = assigned

        return entities


entity_classification_service = EntityClassificationService()
