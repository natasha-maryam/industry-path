import unittest

from models.document_pipeline import SegmentedDocumentBlock
from services.tag_extraction_service import tag_extraction_service


class TagExtractionServiceTests(unittest.TestCase):
    def test_extracts_unique_tags_with_section_reference_and_confidence_metadata(self) -> None:
        blocks = [
            SegmentedDocumentBlock(
                section_id="sec-1",
                block_id="sec-1",
                file_id="doc-1",
                file_name="narrative.pdf",
                document_id="doc-1",
                document_type="control_narrative",
                kind="narrative",
                page=1,
                page_number=1,
                block_type="narrative_section",
                text="AIT-2301 controls FCV-2301 and AIT-2301 is primary.",
                source_references=["narrative.pdf:p1:narrative_section:1"],
            )
        ]

        results = tag_extraction_service.extract(blocks)

        self.assertEqual({item.normalized_tag for item in results}, {"AIT-2301", "FCV-2301"})
        self.assertTrue(all(item.source_section_id == "sec-1" for item in results))
        self.assertTrue(all(item.source_section_reference == "narrative.pdf:p1:narrative_section:1" for item in results))
        self.assertTrue(all(item.confidence_metadata.get("extractor") == "tag_extraction_service" for item in results))
        result_by_tag = {item.normalized_tag: item for item in results}
        self.assertEqual(result_by_tag["AIT-2301"].normalized_equipment, "analyzer")
        self.assertEqual(result_by_tag["AIT-2301"].normalized_type, "analyzer")
        self.assertEqual(result_by_tag["FCV-2301"].normalized_equipment, "flow_control_valve")
        self.assertEqual(result_by_tag["FCV-2301"].normalized_type, "control_valve")
        self.assertEqual(result_by_tag["FCV-2301"].confidence_metadata.get("matched_pattern"), "tag:FCV")


if __name__ == "__main__":
    unittest.main()
