from __future__ import annotations

import logging

from models.document_pipeline import ExtractedTagRecord, SegmentedDocumentBlock
from services.equipment_normalizer_service import equipment_normalizer_service
from services.tag_normalization_service import tag_normalization_service


class TagExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def extract(self, blocks: list[SegmentedDocumentBlock]) -> list[ExtractedTagRecord]:
        records: dict[tuple[str, str, str], ExtractedTagRecord] = {}
        for block in blocks:
            section_reference = block.source_references[0] if block.source_references else block.block_id
            for detection in tag_normalization_service.detect_tags(block.text):
                context = self._context_window(block.text, detection["raw_tag"])
                normalized = equipment_normalizer_service.normalize(
                    tag_name=detection["normalized_tag"],
                    description=context,
                    fallback_type=detection["canonical_type"],
                )
                key = (detection["normalized_tag"], block.block_id, detection["raw_tag"].upper())
                records[key] = ExtractedTagRecord(
                    normalized_tag=detection["normalized_tag"],
                    raw_tag=detection["raw_tag"],
                    family=detection["family"],
                    canonical_type=normalized.normalized_type,
                    normalized_equipment=normalized.normalized_equipment,
                    normalized_type=normalized.normalized_type,
                    matched_pattern=normalized.matched_pattern,
                    source_section_id=block.section_id,
                    source_section_reference=section_reference,
                    source_block_id=block.block_id,
                    source_file_id=block.file_id,
                    source_file_name=block.file_name,
                    source_page=block.page_number,
                    source_text=context[:400],
                    confidence=max(0.9 if block.block_type in {"table", "pid_zone"} else 0.82, normalized.confidence),
                    confidence_metadata={
                        "extractor": "tag_extraction_service",
                        "block_kind": block.kind,
                        "document_type": block.document_type,
                        "matched_pattern": normalized.matched_pattern,
                    },
                )
        results = sorted(records.values(), key=lambda item: (item.normalized_tag, item.source_file_name, item.source_page, item.source_block_id, item.raw_tag))
        self.logger.info("Tag extraction: blocks=%s extracted_tags=%s", len(blocks), len(results))
        return results

    @staticmethod
    def _context_window(text: str, raw_tag: str, radius: int = 96) -> str:
        index = text.upper().find(raw_tag.upper())
        if index < 0:
            return text
        start = max(0, index - radius)
        end = min(len(text), index + len(raw_tag) + radius)
        return text[start:end]


tag_extraction_service = TagExtractionService()
