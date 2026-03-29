import unittest

from models.document_pipeline import ExtractedControlIntentRecord, NormalizedIntentRecord, StructuredExtractionLayerResult
from models.pipeline import EngineeringEntity, InferredRelationship
from services.semantic_behavior_layer import semantic_behavior_layer


class SemanticBehaviorLayerTests(unittest.TestCase):
    def test_normalizes_semantic_intents_with_provenance_and_standardized_verb(self) -> None:
        structured = StructuredExtractionLayerResult(
            extracted_control_intents=[
                ExtractedControlIntentRecord(
                    intent_type="pressure_control",
                    normalized_verb="controls",
                    source_tag="PIT-3001",
                    target_tag="PCV-3001",
                    related_tags=["PIT-3001", "PCV-3001"],
                    source_section_id="sec-7",
                    source_section_reference="narrative.pdf:p7:narrative_section:1",
                    source_block_id="sec-7",
                    source_file_id="doc-7",
                    source_file_name="narrative.pdf",
                    source_page=7,
                    source_text="PIT-3001 regulates pressure through PCV-3001",
                    confidence=0.83,
                )
            ]
        )
        entities = [
            EngineeringEntity(id="PIT-3001", tag="PIT-3001", canonical_type="pressure_transmitter", display_name="PIT-3001", process_unit="clarifier"),
            EngineeringEntity(id="PCV-3001", tag="PCV-3001", canonical_type="control_valve", display_name="PCV-3001", process_unit="clarifier"),
        ]

        results = semantic_behavior_layer._normalize_intents(structured, entities)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].intent_type, "pressure_control")
        self.assertEqual(results[0].normalized_verb, "controls")
        self.assertEqual(results[0].source_section_reference, "narrative.pdf:p7:narrative_section:1")
        self.assertEqual(results[0].source_page, 7)
        self.assertEqual(results[0].source_file_name, "narrative.pdf")
        self.assertEqual(results[0].support_count, 3)
        self.assertGreaterEqual(results[0].confidence, 0.83)

    def test_detects_behavioral_chain_from_sensor_actuator_process_evidence(self) -> None:
        semantic_behavior_layer._structured_tag_metadata = {
            "FIT-1001": {"normalized_equipment": "flow_transmitter", "normalized_type": "flow_transmitter"},
            "FCV-1001": {"normalized_equipment": "control_valve", "normalized_type": "control_valve"},
            "BASIN-1": {"normalized_equipment": "aeration_basin", "normalized_type": "basin"},
        }
        entities = [
            EngineeringEntity(id="FIT-1001", tag="FIT-1001", canonical_type="flow_transmitter", display_name="FIT-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="FCV-1001", tag="FCV-1001", canonical_type="control_valve", display_name="FCV-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="BASIN-1", tag="BASIN-1", canonical_type="basin", display_name="Basin 1", process_unit="BASIN-1", is_synthetic=True),
        ]
        intents = [
            NormalizedIntentRecord(
                intent_id="intent:block-1:1",
                intent_type="flow_control",
                normalized_verb="controls",
                source_tag="FIT-1001",
                target_tag="FCV-1001",
                related_tags=["FIT-1001", "FCV-1001", "BASIN-1"],
                source_text="FIT-1001 controls FCV-1001 to maintain basin flow.",
                source_section_id="sec-1",
                source_section_reference="narrative.pdf:p1:narrative_section:1",
                source_block_id="block-1",
                source_file_id="doc-1",
                source_file_name="narrative.pdf",
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
                confidence_score=0.9,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIT-1001 controls FCV-1001.",
                source_references=["FIT-1001 controls FCV-1001."],
            ),
            InferredRelationship(
                relationship_type="MEASURES",
                source_entity="FIT-1001",
                target_entity="BASIN-1",
                confidence_score=0.84,
                confidence_level="HIGH",
                inference_source="assignment",
                explanation="FIT-1001 measures basin flow.",
                source_references=["process_unit:BASIN-1"],
            ),
            InferredRelationship(
                relationship_type="PART_OF",
                source_entity="FCV-1001",
                target_entity="BASIN-1",
                confidence_score=0.83,
                confidence_level="HIGH",
                inference_source="assignment",
                explanation="FCV-1001 belongs to basin 1.",
                source_references=["process_unit:BASIN-1"],
            ),
        ]

        results = semantic_behavior_layer._detect_behavioral_chains(relationships, entities, intents)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].sensor, "FIT-1001")
        self.assertEqual(results[0].actuator, "FCV-1001")
        self.assertEqual(results[0].process, "BASIN-1")
        self.assertEqual(results[0].chain, ["FIT-1001", "FCV-1001", "BASIN-1"])
        self.assertIn("document_text", results[0].support)
        self.assertIn("graph_topology", results[0].support)
        self.assertTrue(any(item.startswith("measurement_edge:") for item in results[0].evidence))
        self.assertGreater(results[0].confidence, 0.85)


if __name__ == "__main__":
    unittest.main()