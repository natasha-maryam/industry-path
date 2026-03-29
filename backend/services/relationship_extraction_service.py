from __future__ import annotations

import logging
import re

from models.document_pipeline import ExtractedRelationshipRecord, SegmentedDocumentBlock


class RelationshipExtractionService:
    GENERIC_TAG_PATTERN = re.compile(r"\b([A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE)
    FLOW_KEYWORDS = ("flow", "feed", "discharge", "supply", "transfer")

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._verb_patterns = [
            (re.compile(r"\b(?P<source>[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b.{0,60}?\b(?P<verb>controls|control|maintains|maintain|regulates|regulate|modulates|drives)\b.{0,60}?\b(?P<target>[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "CONTROLS", "verb"),
            (re.compile(r"\b(?P<source>[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b.{0,50}?\b(?P<verb>measures|measure|monitors|monitor|senses|sense)\b.{0,60}?\b(?P<target>[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "MEASURES", "verb"),
            (re.compile(r"\b(?P<source>[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b.{0,50}?\b(?P<verb>feeds|feed|discharges to|supplies|supply)\b.{0,60}?\b(?P<target>[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "FEEDS", "verb"),
        ]

    def extract(self, blocks: list[SegmentedDocumentBlock]) -> list[ExtractedRelationshipRecord]:
        relationships: dict[tuple[str, str, str, str], ExtractedRelationshipRecord] = {}
        for block in blocks:
            section_reference = block.source_references[0] if block.source_references else block.block_id
            tags_in_order = [self._normalize_generic_tag(item.group(1)) for item in self.GENERIC_TAG_PATTERN.finditer(block.text)]

            for relationship in self._pattern_based_relationships(block, tags_in_order, section_reference):
                key = (relationship.source_tag, relationship.target_tag, relationship.relationship_type, relationship.source_block_id)
                relationships[key] = relationship

            for relationship in self._verb_based_relationships(block, section_reference):
                key = (relationship.source_tag, relationship.target_tag, relationship.relationship_type, relationship.source_block_id)
                prior = relationships.get(key)
                if prior is None or relationship.confidence > prior.confidence:
                    relationships[key] = relationship

        results = sorted(relationships.values(), key=lambda item: (item.source_tag, item.target_tag, item.relationship_type, item.source_file_name, item.source_page, item.source_block_id))
        self.logger.info("Relationship extraction: blocks=%s extracted_relationships=%s", len(blocks), len(results))
        return results

    def _pattern_based_relationships(self, block: SegmentedDocumentBlock, tags_in_order: list[str], section_reference: str) -> list[ExtractedRelationshipRecord]:
        results: dict[tuple[str, str, str], ExtractedRelationshipRecord] = {}
        if block.block_type in {"pid_zone", "table"}:
            relationship_type = "FEEDS" if any(keyword in block.text.lower() for keyword in self.FLOW_KEYWORDS) else "CONNECTED_TO"
            confidence = 0.8 if block.block_type == "pid_zone" else 0.74
            for left, right in zip(tags_in_order, tags_in_order[1:]):
                if left == right:
                    continue
                key = (left, right, relationship_type)
                results[key] = ExtractedRelationshipRecord(
                    relationship_type=relationship_type,
                    source_tag=left,
                    target_tag=right,
                    source_section_id=block.section_id,
                    source_section_reference=section_reference,
                    source_block_id=block.block_id,
                    source_file_id=block.file_id,
                    source_file_name=block.file_name,
                    source_page=block.page_number,
                    source_text=block.text[:400],
                    confidence=confidence,
                    confidence_metadata={
                        "extractor": "relationship_extraction_service",
                        "method": "tag_pattern",
                        "block_kind": block.kind,
                    },
                )
        return list(results.values())

    def _verb_based_relationships(self, block: SegmentedDocumentBlock, section_reference: str) -> list[ExtractedRelationshipRecord]:
        results: dict[tuple[str, str, str], ExtractedRelationshipRecord] = {}
        for sentence in self._sentence_candidates(block.text):
            for pattern, relationship_type, method in self._verb_patterns:
                for match in pattern.finditer(sentence):
                    source = self._normalize_generic_tag(match.group("source"))
                    target = self._normalize_generic_tag(match.group("target"))
                    if source == target:
                        continue
                    confidence = 0.9 if relationship_type == "CONTROLS" else 0.86 if relationship_type == "MEASURES" else 0.84
                    key = (source, target, relationship_type)
                    results[key] = ExtractedRelationshipRecord(
                        relationship_type=relationship_type,
                        source_tag=source,
                        target_tag=target,
                        source_section_id=block.section_id,
                        source_section_reference=section_reference,
                        source_block_id=block.block_id,
                        source_file_id=block.file_id,
                        source_file_name=block.file_name,
                        source_page=block.page_number,
                        source_text=sentence[:400],
                        raw_verb=match.group("verb").lower(),
                        confidence=confidence,
                        confidence_metadata={
                            "extractor": "relationship_extraction_service",
                            "method": method,
                            "block_kind": block.kind,
                        },
                    )
        return list(results.values())

    @staticmethod
    def _sentence_candidates(text: str) -> list[str]:
        return [segment.strip() for segment in re.split(r"[\n.;]+", text) if segment.strip()]

    @staticmethod
    def _normalize_generic_tag(value: str) -> str:
        token = re.sub(r"\s+", "-", value.strip().upper().replace("_", "-"))
        return re.sub(r"[^A-Z0-9-]", "", token)


relationship_extraction_service = RelationshipExtractionService()
