import unittest

from models.document_pipeline import SegmentedDocumentBlock
from services.relationship_extraction_service import relationship_extraction_service


class RelationshipExtractionServiceTests(unittest.TestCase):
    def test_extracts_flow_control_and_measurement_relationships(self) -> None:
        blocks = [
            SegmentedDocumentBlock(
                section_id="sec-3",
                block_id="sec-3",
                file_id="doc-3",
                file_name="mixed.pdf",
                document_id="doc-3",
                document_type="pid_pdf",
                kind="table",
                page=3,
                page_number=3,
                block_type="table",
                text="FIT-2301   FCV-2301   TK-2301",
                table_rows=[["FIT-2301", "FCV-2301", "TK-2301"]],
                source_references=["mixed.pdf:p3:table:1"],
            ),
            SegmentedDocumentBlock(
                section_id="sec-4",
                block_id="sec-4",
                file_id="doc-3",
                file_name="mixed.pdf",
                document_id="doc-3",
                document_type="control_narrative",
                kind="narrative",
                page=3,
                page_number=3,
                block_type="narrative_section",
                text="PIT-3001 measures XV-3001. AIT-2201 controls FCV-2201.",
                source_references=["mixed.pdf:p3:narrative_section:2"],
            ),
        ]

        results = relationship_extraction_service.extract(blocks)
        relationship_types = {(item.source_tag, item.relationship_type, item.target_tag) for item in results}

        self.assertIn(("FIT-2301", "CONNECTED_TO", "FCV-2301"), relationship_types)
        self.assertIn(("PIT-3001", "MEASURES", "XV-3001"), relationship_types)
        self.assertIn(("AIT-2201", "CONTROLS", "FCV-2201"), relationship_types)
        self.assertTrue(all(item.source_section_reference for item in results))
        self.assertTrue(all(item.confidence_metadata.get("extractor") == "relationship_extraction_service" for item in results))


if __name__ == "__main__":
    unittest.main()
