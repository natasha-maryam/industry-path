import unittest

from models.pipeline import RawDocumentChunk
from services.control_intent_extraction_service import control_intent_extraction_service
from services.document_segmentation_service import document_segmentation_service
from services.relationship_extraction_service import relationship_extraction_service
from services.tag_extraction_service import tag_extraction_service


class DocumentSegmentationTests(unittest.TestCase):
    def test_narrative_only_control_narrative_pdf_returns_narrative_sections(self) -> None:
        chunks = [
            RawDocumentChunk(
                file_id="doc-narrative",
                file_name="control-narrative.pdf",
                document_type="control_narrative",
                page_number=1,
                text="CONTROL PHILOSOPHY\nAIT-2301 maintains dissolved oxygen by modulating FCV-2301.\nStartup occurs in auto mode.",
            )
        ]

        documents = document_segmentation_service.segment_chunks(chunks)

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].document_id, "doc-narrative")
        self.assertTrue(documents[0].sections)
        self.assertTrue(all(section.kind == "narrative" for section in documents[0].sections))
        self.assertTrue(any("AIT-2301 maintains" in section.text for section in documents[0].sections))

    def test_pid_heavy_pdf_returns_tables_and_pid_zones(self) -> None:
        chunks = [
            RawDocumentChunk(
                file_id="doc-pid",
                file_name="plant-pid.pdf",
                document_type="pid_pdf",
                page_number=2,
                text="AERATION BASIN ZONE\nFIT-2301   FCV-2301   BAS-01\nPMP-1001   TK-1001   XV-1001\nFlow loop notes for zone control.",
            )
        ]

        documents = document_segmentation_service.segment_chunks(chunks)
        kinds = {section.kind for section in documents[0].sections}

        self.assertIn("pid_zone", kinds)
        self.assertIn("table", kinds)
        self.assertIn("narrative", kinds)
        zone_sections = [section for section in documents[0].sections if section.kind == "pid_zone"]
        self.assertTrue(any(section.page == 2 for section in zone_sections))
        self.assertTrue(any(section.metadata.get("source_span") for section in zone_sections))

    def test_mixed_docs_preserve_document_boundaries_and_feed_structured_extractors(self) -> None:
        chunks = [
            RawDocumentChunk(
                file_id="doc-mixed-1",
                file_name="mixed-narrative.pdf",
                document_type="control_narrative",
                page_number=1,
                text="INTERLOCKS\nLIT-2001 regulates PMP-2001 when level is high.\nTAG   DESC   VALUE\nLIT-2001   Level   High",
            ),
            RawDocumentChunk(
                file_id="doc-mixed-2",
                file_name="mixed-pid.pdf",
                document_type="pid_pdf",
                page_number=3,
                text="CLARIFIER AREA\nPIT-3001   XV-3001   CL-3001\nPressure loop controls outlet valve.",
            ),
        ]

        segmented_documents = document_segmentation_service.segment_chunks(chunks)
        flattened = document_segmentation_service.flatten_sections(segmented_documents)

        self.assertEqual({document.document_id for document in segmented_documents}, {"doc-mixed-1", "doc-mixed-2"})
        self.assertTrue(any(section.kind == "table" for section in flattened))
        self.assertTrue(any(section.kind == "pid_zone" for section in flattened if section.document_id == "doc-mixed-2"))

        extracted_tags = tag_extraction_service.extract(flattened)
        extracted_relationships = relationship_extraction_service.extract(flattened)
        extracted_control_intents = control_intent_extraction_service.extract(flattened)

        self.assertTrue(extracted_tags)
        self.assertTrue(all(tag.source_block_id in {section.block_id for section in flattened} for tag in extracted_tags))
        self.assertTrue(extracted_relationships)
        self.assertTrue(all(rel.source_block_id in {section.block_id for section in flattened} for rel in extracted_relationships))
        self.assertTrue(extracted_control_intents)


if __name__ == "__main__":
    unittest.main()