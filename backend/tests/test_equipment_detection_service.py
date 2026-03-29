import unittest

from models.document_pipeline import SegmentedDocumentBlock
from services.equipment_detection_service import equipment_detection_service


class EquipmentDetectionServiceTests(unittest.TestCase):
    def test_detects_normalized_equipment_without_duplicates(self) -> None:
        blocks = [
            SegmentedDocumentBlock(
                section_id="sec-2",
                block_id="sec-2",
                file_id="doc-2",
                file_name="pid.pdf",
                document_id="doc-2",
                document_type="pid_pdf",
                kind="table",
                page=2,
                page_number=2,
                block_type="table",
                text="PMP-1001   TK-1001   PMP-1001",
                table_rows=[["PMP-1001", "TK-1001", "PMP-1001"]],
                source_references=["pid.pdf:p2:table:1"],
            )
        ]

        results = equipment_detection_service.extract(blocks)

        self.assertEqual({item.normalized_tag for item in results}, {"PMP-1001", "TK-1001"})
        self.assertTrue(all(item.source_section_reference == "pid.pdf:p2:table:1" for item in results))
        self.assertTrue(all(item.confidence_metadata.get("extractor") == "equipment_detection_service" for item in results))
        result_by_tag = {item.normalized_tag: item for item in results}
        self.assertEqual(result_by_tag["PMP-1001"].normalized_name, "pump")
        self.assertEqual(result_by_tag["PMP-1001"].canonical_type, "pump")
        self.assertEqual(result_by_tag["TK-1001"].normalized_name, "tank")
        self.assertEqual(result_by_tag["TK-1001"].canonical_type, "tank")
        self.assertEqual(result_by_tag["PMP-1001"].matched_pattern, "tag:PMP")



if __name__ == "__main__":
    unittest.main()
