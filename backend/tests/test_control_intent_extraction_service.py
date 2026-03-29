import unittest

from models.document_pipeline import SegmentedDocumentBlock
from services.control_intent_extraction_service import control_intent_extraction_service


class ControlIntentExtractionServiceTests(unittest.TestCase):
    def test_extracts_flow_level_pressure_and_temperature_intents(self) -> None:
        blocks = [
            SegmentedDocumentBlock(
                section_id="sec-5",
                block_id="sec-5",
                file_id="doc-4",
                file_name="intent.pdf",
                document_id="doc-4",
                document_type="control_narrative",
                kind="narrative",
                page=4,
                page_number=4,
                block_type="narrative_section",
                text=(
                    "FIT-2301 controls flow through FCV-2301. "
                    "LIT-2001 regulates level via PMP-2001. "
                    "PIT-3001 maintains pressure with XV-3001. "
                    "TT-4101 controls temperature through TCV-4101."
                ),
                source_references=["intent.pdf:p4:narrative_section:1"],
            )
        ]

        results = control_intent_extraction_service.extract(blocks)
        intent_types = {item.intent_type for item in results}

        self.assertEqual(intent_types, {"flow_control", "level_control", "pressure_control", "temperature_control"})
        self.assertTrue(all(item.source_section_reference == "intent.pdf:p4:narrative_section:1" for item in results))
        self.assertTrue(all(item.confidence_metadata.get("extractor") == "control_intent_extraction_service" for item in results))
        normalized_verbs = {item.intent_type: item.normalized_verb for item in results}
        self.assertEqual(normalized_verbs["flow_control"], "controls")
        self.assertEqual(normalized_verbs["level_control"], "controls")
        self.assertEqual(normalized_verbs["pressure_control"], "controls")
        self.assertEqual(normalized_verbs["temperature_control"], "controls")

    def test_extracts_intents_from_table_content_with_consistent_normalization(self) -> None:
        blocks = [
            SegmentedDocumentBlock(
                section_id="sec-6",
                block_id="sec-6",
                file_id="doc-6",
                file_name="intent-table.pdf",
                document_id="doc-6",
                document_type="control_narrative",
                kind="table",
                page=5,
                page_number=5,
                block_type="table",
                text="control summary table",
                table_rows=[
                    ["LIT-1101", "maintains level", "PMP-1101"],
                    ["PIT-1201", "regulates pressure", "PCV-1201"],
                ],
                source_references=["intent-table.pdf:p5:table:1"],
            )
        ]

        results = control_intent_extraction_service.extract(blocks)

        self.assertEqual({item.intent_type for item in results}, {"level_control", "pressure_control"})
        self.assertTrue(all(item.normalized_verb == "controls" for item in results))
        self.assertTrue(all(item.source_page == 5 for item in results))
        self.assertTrue(all(item.source_section_reference == "intent-table.pdf:p5:table:1" for item in results))


if __name__ == "__main__":
    unittest.main()
