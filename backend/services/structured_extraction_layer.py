from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from models.document_pipeline import StructuredExtractionLayerResult
from services.control_intent_extraction_service import control_intent_extraction_service
from services.document_segmentation_service import document_segmentation_service
from services.equipment_detection_service import equipment_detection_service
from services.extraction_merge_service import extraction_merge_service
from services.relationship_extraction_service import relationship_extraction_service
from services.tag_extraction_service import tag_extraction_service


class StructuredExtractionLayer:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def process(self, files: list[dict], resolve_file_path) -> StructuredExtractionLayerResult:
        segmented_documents, pid_chunks, narrative_chunks = document_segmentation_service.segment_documents(files, resolve_file_path)
        blocks = document_segmentation_service.flatten_sections(segmented_documents)
        warnings: list[str] = []
        if not blocks:
            warnings.append("Structured extraction produced no segmented blocks.")

        with ThreadPoolExecutor(max_workers=4) as executor:
            tags_future = executor.submit(tag_extraction_service.extract, blocks)
            equipment_future = executor.submit(equipment_detection_service.extract, blocks)
            relationships_future = executor.submit(relationship_extraction_service.extract, blocks)
            intents_future = executor.submit(control_intent_extraction_service.extract, blocks)

            extracted_tags = tags_future.result()
            extracted_equipment = equipment_future.result()
            extracted_relationships = relationships_future.result()
            extracted_control_intents = intents_future.result()

        merge_result = extraction_merge_service.merge(
            extracted_tags=extracted_tags,
            extracted_equipment=extracted_equipment,
            extracted_relationships=extracted_relationships,
            extracted_control_intents=extracted_control_intents,
        )

        self.logger.info(
            "Structured extraction layer: blocks=%s tags=%s equipment=%s relationships=%s intents=%s",
            len(blocks),
            len(extracted_tags),
            len(extracted_equipment),
            len(extracted_relationships),
            len(extracted_control_intents),
        )
        return StructuredExtractionLayerResult(
            pid_chunks=pid_chunks,
            narrative_chunks=narrative_chunks,
            segmented_documents=segmented_documents,
            blocks=blocks,
            extracted_tags=extracted_tags,
            extracted_equipment=extracted_equipment,
            equipment_detections=extracted_equipment,
            extracted_relationships=extracted_relationships,
            extracted_control_intents=extracted_control_intents,
            merge_result=merge_result,
            warnings=warnings,
        )


structured_extraction_layer = StructuredExtractionLayer()
