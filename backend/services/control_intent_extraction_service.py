from __future__ import annotations

import logging
import re

from models.document_pipeline import ExtractedControlIntentRecord, SegmentedDocumentBlock
from services.semantic_normalization_service import semantic_normalization_service


class ControlIntentExtractionService:
    GENERIC_TAG_PATTERN = re.compile(r"\b([A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE)

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def extract(self, blocks: list[SegmentedDocumentBlock]) -> list[ExtractedControlIntentRecord]:
        intents: dict[tuple[str, str, str, str], ExtractedControlIntentRecord] = {}
        for block in blocks:
            section_reference = block.source_references[0] if block.source_references else block.block_id
            for sentence in self._content_candidates(block):
                tags = [self._normalize_generic_tag(match.group(1)) for match in self.GENERIC_TAG_PATTERN.finditer(sentence)]
                intent_type = semantic_normalization_service.detect_intent_type(sentence, tags)
                if intent_type is None:
                    continue
                verb = semantic_normalization_service.normalize_verb(sentence)
                if verb is None:
                    continue
                key = (block.block_id, intent_type, tags[0] if tags else "", tags[1] if len(tags) > 1 else "")
                intents[key] = ExtractedControlIntentRecord(
                    intent_type=intent_type,
                    normalized_verb=verb,
                    source_tag=tags[0] if len(tags) >= 1 else None,
                    target_tag=tags[1] if len(tags) >= 2 else None,
                    related_tags=tags,
                    source_section_id=block.section_id,
                    source_section_reference=section_reference,
                    source_block_id=block.block_id,
                    source_file_id=block.file_id,
                    source_file_name=block.file_name,
                    source_page=block.page_number,
                    source_text=sentence[:400],
                    confidence=0.86 if len(tags) >= 2 else 0.74,
                    confidence_metadata={
                        "extractor": "control_intent_extraction_service",
                        "block_kind": block.kind,
                        "intent_type": intent_type,
                        "normalized_verb": verb,
                        "method": "semantic_phrase_pattern",
                    },
                )
        results = sorted(intents.values(), key=lambda item: (item.intent_type, item.source_file_name, item.source_page, item.source_block_id, item.source_text))
        self.logger.info("Control intent extraction: blocks=%s extracted_control_intents=%s", len(blocks), len(results))
        return results

    @staticmethod
    def _sentence_candidates(text: str) -> list[str]:
        return [segment.strip() for segment in re.split(r"[\n.;]+", text) if segment.strip()]

    @staticmethod
    def _content_candidates(block: SegmentedDocumentBlock) -> list[str]:
        candidates = ControlIntentExtractionService._sentence_candidates(block.text)
        if block.table_rows:
            for row in block.table_rows:
                joined = " ".join(str(cell).strip() for cell in row if str(cell).strip())
                if joined:
                    candidates.extend(ControlIntentExtractionService._sentence_candidates(joined))
        deduped: list[str] = []
        for item in candidates:
            if item not in deduped:
                deduped.append(item)
        return deduped

    @staticmethod
    def _normalize_generic_tag(value: str) -> str:
        token = re.sub(r"\s+", "-", value.strip().upper().replace("_", "-"))
        return re.sub(r"[^A-Z0-9-]", "", token)


control_intent_extraction_service = ControlIntentExtractionService()
