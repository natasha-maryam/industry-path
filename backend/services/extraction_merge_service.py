from __future__ import annotations

import logging

from models.document_pipeline import (
    ExtractedControlIntentRecord,
    ExtractedRelationshipRecord,
    ExtractedTagRecord,
    ExtractionMergeResult,
    IntermediateEdgeCandidate,
    IntermediateNodeCandidate,
    NormalizedEquipmentRecord,
)
from services.parser_relationship_graph_service import parser_relationship_graph_service


class ExtractionMergeService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def merge(
        self,
        *,
        extracted_tags: list[ExtractedTagRecord],
        extracted_equipment: list[NormalizedEquipmentRecord],
        extracted_relationships: list[ExtractedRelationshipRecord],
        extracted_control_intents: list[ExtractedControlIntentRecord],
    ) -> ExtractionMergeResult:
        node_candidates = self._merge_nodes(extracted_tags, extracted_equipment)
        edge_candidates = self._merge_edges(extracted_relationships, extracted_control_intents)
        graph = parser_relationship_graph_service.build(node_candidates, edge_candidates)
        self.logger.info(
            "Extraction merge: node_candidates=%s edge_candidates=%s graph_edges=%s",
            len(node_candidates),
            len(edge_candidates),
            len(graph.edges),
        )
        return ExtractionMergeResult(node_candidates=node_candidates, edge_candidates=edge_candidates, graph=graph)

    def _merge_nodes(
        self,
        extracted_tags: list[ExtractedTagRecord],
        extracted_equipment: list[NormalizedEquipmentRecord],
    ) -> list[IntermediateNodeCandidate]:
        merged: dict[str, IntermediateNodeCandidate] = {}
        for equipment in extracted_equipment:
            merged[equipment.normalized_tag] = IntermediateNodeCandidate(
                candidate_id=f"node:{equipment.normalized_tag}",
                normalized_tag=equipment.normalized_tag,
                canonical_type=equipment.canonical_type,
                display_name=equipment.normalized_name,
                normalized_equipment=equipment.normalized_name,
                normalized_type=equipment.canonical_type,
                source_section_ids=[equipment.source_section_id],
                source_section_references=[equipment.source_section_reference],
                source_pages=[equipment.source_page],
                source_texts=[equipment.source_text],
                confidence=equipment.confidence,
                confidence_metadata={
                    "sources": [equipment.confidence_metadata],
                    "merge_source": "equipment",
                },
            )

        for tag in extracted_tags:
            node = merged.get(tag.normalized_tag)
            if node is None:
                merged[tag.normalized_tag] = IntermediateNodeCandidate(
                    candidate_id=f"node:{tag.normalized_tag}",
                    normalized_tag=tag.normalized_tag,
                    canonical_type=tag.canonical_type,
                    display_name=tag.normalized_tag,
                    normalized_equipment=tag.normalized_equipment,
                    normalized_type=tag.normalized_type,
                    source_section_ids=[tag.source_section_id],
                    source_section_references=[tag.source_section_reference],
                    source_pages=[tag.source_page],
                    source_texts=[tag.source_text],
                    confidence=tag.confidence,
                    confidence_metadata={
                        "sources": [tag.confidence_metadata],
                        "merge_source": "tag",
                    },
                )
                continue
            self._append_unique(node.source_section_ids, tag.source_section_id)
            self._append_unique(node.source_section_references, tag.source_section_reference)
            self._append_unique(node.source_pages, tag.source_page)
            self._append_unique(node.source_texts, tag.source_text)
            if not node.normalized_equipment and tag.normalized_equipment:
                node.normalized_equipment = tag.normalized_equipment
            if not node.normalized_type and tag.normalized_type:
                node.normalized_type = tag.normalized_type
            node.confidence = max(node.confidence, tag.confidence)
            node.confidence_metadata.setdefault("sources", [])
            node.confidence_metadata["sources"].append(tag.confidence_metadata)

        return sorted(merged.values(), key=lambda item: item.normalized_tag)

    def _merge_edges(
        self,
        extracted_relationships: list[ExtractedRelationshipRecord],
        extracted_control_intents: list[ExtractedControlIntentRecord],
    ) -> list[IntermediateEdgeCandidate]:
        merged: dict[tuple[str, str, str], IntermediateEdgeCandidate] = {}
        for relationship in extracted_relationships:
            key = (relationship.source_tag, relationship.target_tag, relationship.relationship_type)
            merged[key] = IntermediateEdgeCandidate(
                candidate_id=f"edge:{relationship.source_tag}:{relationship.relationship_type}:{relationship.target_tag}",
                relationship_type=relationship.relationship_type,
                source_tag=relationship.source_tag,
                target_tag=relationship.target_tag,
                raw_relationship_types=[relationship.relationship_type],
                source_section_ids=[relationship.source_section_id],
                source_section_references=[relationship.source_section_reference],
                source_pages=[relationship.source_page],
                source_texts=[relationship.source_text],
                raw_verbs=[relationship.raw_verb] if relationship.raw_verb else [],
                confidence=relationship.confidence,
                confidence_metadata={"sources": [{**relationship.confidence_metadata, "confidence": relationship.confidence}]},
            )

        for intent in extracted_control_intents:
            if not intent.source_tag or not intent.target_tag:
                continue
            key = (intent.source_tag, intent.target_tag, "CONTROLS")
            edge = merged.get(key)
            if edge is None:
                merged[key] = IntermediateEdgeCandidate(
                    candidate_id=f"edge:{intent.source_tag}:CONTROLS:{intent.target_tag}",
                    relationship_type="CONTROLS",
                    source_tag=intent.source_tag,
                    target_tag=intent.target_tag,
                    raw_relationship_types=["CONTROLS"],
                    source_section_ids=[intent.source_section_id],
                    source_section_references=[intent.source_section_reference],
                    source_pages=[intent.source_page],
                    source_texts=[intent.source_text],
                    related_intent_types=[intent.intent_type],
                    confidence=intent.confidence,
                    confidence_metadata={"sources": [{**intent.confidence_metadata, "method": "intent", "confidence": intent.confidence}], "merged_from_intent": True},
                )
                continue
            self._append_unique(edge.source_section_ids, intent.source_section_id)
            self._append_unique(edge.source_section_references, intent.source_section_reference)
            self._append_unique(edge.source_pages, intent.source_page)
            self._append_unique(edge.source_texts, intent.source_text)
            self._append_unique(edge.related_intent_types, intent.intent_type)
            self._append_unique(edge.raw_relationship_types, "CONTROLS")
            edge.confidence = max(edge.confidence, intent.confidence)
            edge.confidence_metadata.setdefault("sources", [])
            edge.confidence_metadata["sources"].append({**intent.confidence_metadata, "method": "intent", "confidence": intent.confidence})

        return sorted(merged.values(), key=lambda item: (item.source_tag, item.target_tag, item.relationship_type))

    @staticmethod
    def _append_unique(values: list, value) -> None:
        if value not in values:
            values.append(value)


extraction_merge_service = ExtractionMergeService()
