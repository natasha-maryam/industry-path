import unittest

from models.document_pipeline import NormalizedIntentRecord, PipelineControlLoopRecord
from models.pipeline import EngineeringEntity, InferredRelationship
from services.cross_validation_service import cross_validation_service


class CrossValidationServiceTests(unittest.TestCase):
    def test_accepts_relationship_with_two_support_signals(self) -> None:
        entities = [
            EngineeringEntity(id="FIT-1001", tag="FIT-1001", canonical_type="flow_transmitter", display_name="FIT-1001", process_unit="basin-1"),
            EngineeringEntity(id="FCV-1001", tag="FCV-1001", canonical_type="control_valve", display_name="FCV-1001", process_unit="basin-1"),
        ]
        intents = [
            NormalizedIntentRecord(
                intent_id="intent:1",
                intent_type="flow_control",
                normalized_verb="controls",
                source_tag="FIT-1001",
                target_tag="FCV-1001",
                related_tags=["FIT-1001", "FCV-1001"],
                source_text="FIT-1001 controls flow through FCV-1001",
                source_section_id="sec-1",
                source_section_reference="doc:p1:s1",
                source_block_id="block-1",
                source_file_id="doc-1",
                source_file_name="doc.pdf",
                source_page=1,
                support=["document_text", "graph_topology", "tag_naming_pattern"],
                support_count=3,
                confidence=0.88,
            )
        ]
        relationships = [
            InferredRelationship(
                relationship_type="CONTROLS",
                source_entity="FIT-1001",
                target_entity="FCV-1001",
                confidence_score=0.86,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="Candidate control relationship.",
                source_references=["doc:p1:s1"],
            )
        ]

        validated, rejected, debug = cross_validation_service.validate_relationships(relationships, entities, intents)

        self.assertEqual(len(validated), 1)
        self.assertEqual(len(rejected), 0)
        self.assertEqual(debug[0].support_count, 3)
        self.assertTrue(debug[0].text_support.supported)
        self.assertTrue(debug[0].topology_support.supported)
        self.assertTrue(debug[0].naming_support.supported)

    def test_rejects_relationship_with_single_support_signal_and_records_reasons(self) -> None:
        entities = [
            EngineeringEntity(id="AIT-2001", tag="AIT-2001", canonical_type="analyzer", display_name="AIT-2001", process_unit="basin-1"),
            EngineeringEntity(id="BL-9001", tag="BL-9001", canonical_type="blower", display_name="BL-9001", process_unit="blower-package"),
        ]
        relationships = [
            InferredRelationship(
                relationship_type="CONTROLS",
                source_entity="AIT-2001",
                target_entity="BL-9001",
                confidence_score=0.62,
                confidence_level="MEDIUM",
                inference_source="heuristic",
                explanation="Weak heuristic candidate.",
                source_references=["heuristic-locality"],
            )
        ]

        validated, rejected, debug = cross_validation_service.validate_relationships(relationships, entities, intents=[])

        self.assertEqual(len(validated), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(debug[0].support_count, 1)
        self.assertIn("missing_graph_topology_support", debug[0].rejection_reasons)
        self.assertIn("missing_tag_naming_support", debug[0].rejection_reasons)
        self.assertIn("support_count_below_threshold", debug[0].rejection_reasons)

    def test_rejects_loop_with_single_support_signal_and_exposes_debug(self) -> None:
        entities = [
            EngineeringEntity(id="FIT-3001", tag="FIT-3001", canonical_type="flow_transmitter", display_name="FIT-3001", process_unit="basin-1"),
            EngineeringEntity(id="XV-9001", tag="XV-9001", canonical_type="valve", display_name="XV-9001", process_unit="remote-area"),
        ]
        loops = [
            PipelineControlLoopRecord(
                loop_id="loop:FIT-3001:XV-9001:remote-line",
                name="FIT-3001 -> XV-9001 -> remote-line",
                sensor_tag="FIT-3001",
                chain=["FIT-3001", "CTRL_3001", "XV-9001", "remote-line"],
                actuator_tag="XV-9001",
                process_node="remote-line",
                controller_tag="CTRL_3001",
                intent_type="flow_control",
                source_texts=["FIT-3001 controls flow through XV-9001"],
                support=["document_text"],
                support_count=1,
                confidence=0.82,
                tuning_confidence=0.41,
            )
        ]

        validated, rejected, debug = cross_validation_service.validate_loops(loops, entities)

        self.assertEqual(len(validated), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(debug[0].support_count, 1)
        self.assertTrue(debug[0].text_support.supported)
        self.assertFalse(debug[0].topology_support.supported)
        self.assertFalse(debug[0].naming_support.supported)
        self.assertIn("support_count_below_threshold", debug[0].rejection_reasons)


if __name__ == "__main__":
    unittest.main()