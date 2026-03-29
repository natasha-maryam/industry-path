import unittest

from models.document_pipeline import (
    ExtractedControlIntentRecord,
    ExtractedRelationshipRecord,
    ExtractedTagRecord,
    NormalizedEquipmentRecord,
)
from services.extraction_merge_service import extraction_merge_service


class ExtractionMergeServiceTests(unittest.TestCase):
    def test_merge_consolidates_outputs_into_intermediate_graph_candidates(self) -> None:
        extracted_tags = [
            ExtractedTagRecord(
                normalized_tag="AIT-2301",
                raw_tag="AIT-2301",
                family="AIT",
                canonical_type="analyzer",
                source_section_id="sec-a",
                source_section_reference="doc:p1:s1",
                source_block_id="sec-a",
                source_file_id="doc-5",
                source_file_name="doc.pdf",
                source_page=1,
                source_text="AIT-2301 controls FCV-2301",
                confidence=0.82,
            )
        ]
        extracted_equipment = [
            NormalizedEquipmentRecord(
                normalized_tag="AIT-2301",
                canonical_type="analyzer",
                normalized_name="AIT-2301",
                source_section_id="sec-a",
                source_section_reference="doc:p1:s1",
                source_block_id="sec-a",
                source_file_id="doc-5",
                source_file_name="doc.pdf",
                source_page=1,
                source_text="AIT-2301 controls FCV-2301",
                confidence=0.88,
            )
        ]
        extracted_relationships = [
            ExtractedRelationshipRecord(
                relationship_type="CONTROLS",
                source_tag="AIT-2301",
                target_tag="FCV-2301",
                source_section_id="sec-a",
                source_section_reference="doc:p1:s1",
                source_block_id="sec-a",
                source_file_id="doc-5",
                source_file_name="doc.pdf",
                source_page=1,
                source_text="AIT-2301 controls FCV-2301",
                raw_verb="controls",
                confidence=0.9,
            )
        ]
        extracted_control_intents = [
            ExtractedControlIntentRecord(
                intent_type="flow_control",
                normalized_verb="controls",
                source_tag="AIT-2301",
                target_tag="FCV-2301",
                related_tags=["AIT-2301", "FCV-2301"],
                source_section_id="sec-a",
                source_section_reference="doc:p1:s1",
                source_block_id="sec-a",
                source_file_id="doc-5",
                source_file_name="doc.pdf",
                source_page=1,
                source_text="AIT-2301 controls flow through FCV-2301",
                confidence=0.86,
            )
        ]

        merged = extraction_merge_service.merge(
            extracted_tags=extracted_tags,
            extracted_equipment=extracted_equipment,
            extracted_relationships=extracted_relationships,
            extracted_control_intents=extracted_control_intents,
        )

        self.assertEqual(len(merged.node_candidates), 1)
        self.assertEqual(len(merged.edge_candidates), 1)
        self.assertEqual(merged.edge_candidates[0].related_intent_types, ["flow_control"])
        self.assertEqual(merged.edge_candidates[0].source_section_references, ["doc:p1:s1"])
        self.assertEqual(len(merged.graph.nodes), 1)
        self.assertEqual(len(merged.graph.edges), 1)
        self.assertEqual(merged.graph.edges[0].relationship_type, "control")
        self.assertEqual(merged.graph.edges[0].evidence_references, ["doc:p1:s1"])
        self.assertEqual(merged.graph.downstream_map, {})



if __name__ == "__main__":
    unittest.main()