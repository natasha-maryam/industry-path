import unittest

from models.document_pipeline import NormalizedIntentRecord
from models.pipeline import EngineeringEntity, InferredRelationship
from services.strict_control_loop_engine import strict_control_loop_engine


class StrictControlLoopEngineTests(unittest.TestCase):
    def test_detects_explicit_controller_loop_from_control_narrative_graph(self) -> None:
        entities = [
            EngineeringEntity(id="FIT-1001", tag="FIT-1001", canonical_type="flow_transmitter", display_name="FIT-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="FIC-1001", tag="FIC-1001", canonical_type="panel", display_name="FIC-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="FCV-1001", tag="FCV-1001", canonical_type="control_valve", display_name="FCV-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="BASIN-1", tag="BASIN-1", canonical_type="basin", display_name="Basin 1", process_unit="BASIN-1", is_synthetic=True),
        ]
        relationships = [
            InferredRelationship(relationship_type="MEASURES", source_entity="FIT-1001", target_entity="BASIN-1", confidence_score=0.9, confidence_level="HIGH", inference_source="narrative", explanation="FIT measures basin flow", source_references=["narrative:p1"]),
            InferredRelationship(relationship_type="SIGNAL_TO", source_entity="FIT-1001", target_entity="FIC-1001", confidence_score=0.88, confidence_level="HIGH", inference_source="narrative", explanation="FIT feeds FIC", source_references=["narrative:p1"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="FIC-1001", target_entity="FCV-1001", confidence_score=0.9, confidence_level="HIGH", inference_source="narrative", explanation="FIC drives FCV", source_references=["narrative:p1"]),
            InferredRelationship(relationship_type="PART_OF", source_entity="FCV-1001", target_entity="BASIN-1", confidence_score=0.84, confidence_level="HIGH", inference_source="assignment", explanation="FCV belongs to basin", source_references=["pid:p2"]),
        ]
        intents = [
            NormalizedIntentRecord(
                intent_id="intent:1",
                intent_type="flow_control",
                normalized_verb="controls",
                source_tag="FIT-1001",
                target_tag="FCV-1001",
                related_tags=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
                source_text="FIT-1001 sends flow signal to FIC-1001 which controls FCV-1001.",
                source_section_id="sec-1",
                source_section_reference="narrative:p1:s1",
                source_block_id="block-1",
                source_file_id="doc-1",
                source_file_name="narrative.pdf",
                source_page=1,
                support=["document_text", "graph_topology"],
                support_count=2,
                confidence=0.9,
            )
        ]
        metadata = {
            "FIC-1001": {"normalized_equipment": "pid_controller", "normalized_type": "controller"},
            "BASIN-1": {"normalized_equipment": "aeration_basin", "normalized_type": "basin"},
        }

        loops, warnings = strict_control_loop_engine.discover(
            entities=entities,
            relationships=relationships,
            metadata_by_entity=metadata,
            intents=intents,
        )

        self.assertEqual(len(loops), 1)
        self.assertEqual(warnings, [])
        self.assertEqual(loops[0].chain, ["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"])
        self.assertEqual(loops[0].controller_tag, "FIC-1001")
        self.assertGreaterEqual(loops[0].completeness_score, 0.99)
        self.assertGreaterEqual(loops[0].continuity_score, 0.99)
        self.assertGreaterEqual(loops[0].validation_score, 0.9)
        self.assertGreaterEqual(loops[0].relationship_score, 0.84)
        self.assertGreaterEqual(loops[0].tuning_confidence, 0.55)

    def test_infers_controller_for_pid_derived_direct_sensor_to_actuator_path(self) -> None:
        entities = [
            EngineeringEntity(id="PIT-2201", tag="PIT-2201", canonical_type="pressure_transmitter", display_name="PIT-2201", process_unit="REACTOR-1"),
            EngineeringEntity(id="PCV-2201", tag="PCV-2201", canonical_type="control_valve", display_name="PCV-2201", process_unit="REACTOR-1"),
            EngineeringEntity(id="REACTOR-1", tag="REACTOR-1", canonical_type="reactor", display_name="Reactor 1", process_unit="REACTOR-1", is_synthetic=True),
        ]
        relationships = [
            InferredRelationship(relationship_type="MEASURES", source_entity="PIT-2201", target_entity="REACTOR-1", confidence_score=0.88, confidence_level="HIGH", inference_source="merged", explanation="PIT measures reactor pressure", source_references=["pid:p4"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="PIT-2201", target_entity="PCV-2201", confidence_score=0.86, confidence_level="HIGH", inference_source="merged", explanation="PIT signal tied to PCV", source_references=["pid:p4"]),
            InferredRelationship(relationship_type="PART_OF", source_entity="PCV-2201", target_entity="REACTOR-1", confidence_score=0.84, confidence_level="HIGH", inference_source="assignment", explanation="PCV belongs to reactor", source_references=["pid:p4"]),
        ]

        loops, warnings = strict_control_loop_engine.discover(
            entities=entities,
            relationships=relationships,
            metadata_by_entity={"REACTOR-1": {"normalized_equipment": "reactor", "normalized_type": "reactor"}},
            intents=[],
        )

        self.assertEqual(len(loops), 1)
        self.assertEqual(warnings, [])
        self.assertEqual(loops[0].chain[0], "PIT-2201")
        self.assertEqual(loops[0].chain[2:], ["PCV-2201", "REACTOR-1"])
        self.assertTrue((loops[0].controller_tag or "").startswith("CTRL_"))

    def test_rejects_partial_loop_without_process(self) -> None:
        entities = [
            EngineeringEntity(id="LIT-3001", tag="LIT-3001", canonical_type="level_transmitter", display_name="LIT-3001", process_unit="TK-1"),
            EngineeringEntity(id="LIC-3001", tag="LIC-3001", canonical_type="panel", display_name="LIC-3001", process_unit="TK-1"),
            EngineeringEntity(id="LV-3001", tag="LV-3001", canonical_type="valve", display_name="LV-3001", process_unit="TK-1"),
        ]
        relationships = [
            InferredRelationship(relationship_type="SIGNAL_TO", source_entity="LIT-3001", target_entity="LIC-3001", confidence_score=0.88, confidence_level="HIGH", inference_source="narrative", explanation="LIT sends signal to LIC", source_references=["narrative:p2"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="LIC-3001", target_entity="LV-3001", confidence_score=0.88, confidence_level="HIGH", inference_source="narrative", explanation="LIC controls LV", source_references=["narrative:p2"]),
        ]
        metadata = {"LIC-3001": {"normalized_equipment": "level_controller", "normalized_type": "controller"}}

        loops, warnings = strict_control_loop_engine.discover(
            entities=entities,
            relationships=relationships,
            metadata_by_entity=metadata,
            intents=[],
        )

        self.assertEqual(loops, [])
        self.assertEqual(warnings, [])

    def test_rejects_inconsistent_chain_when_sensor_does_not_measure_process(self) -> None:
        entities = [
            EngineeringEntity(id="FIT-4001", tag="FIT-4001", canonical_type="flow_transmitter", display_name="FIT-4001", process_unit="BASIN-1"),
            EngineeringEntity(id="FIC-4001", tag="FIC-4001", canonical_type="panel", display_name="FIC-4001", process_unit="BASIN-1"),
            EngineeringEntity(id="FCV-4001", tag="FCV-4001", canonical_type="control_valve", display_name="FCV-4001", process_unit="BASIN-1"),
            EngineeringEntity(id="TK-9", tag="TK-9", canonical_type="tank", display_name="Tank 9", process_unit="TK-9", is_synthetic=True),
        ]
        relationships = [
            InferredRelationship(relationship_type="SIGNAL_TO", source_entity="FIT-4001", target_entity="FIC-4001", confidence_score=0.87, confidence_level="HIGH", inference_source="merged", explanation="FIT to FIC", source_references=["pid:p8"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="FIC-4001", target_entity="FCV-4001", confidence_score=0.87, confidence_level="HIGH", inference_source="merged", explanation="FIC to FCV", source_references=["pid:p8"]),
            InferredRelationship(relationship_type="PART_OF", source_entity="FCV-4001", target_entity="TK-9", confidence_score=0.84, confidence_level="HIGH", inference_source="merged", explanation="FCV part of tank 9", source_references=["pid:p8"]),
        ]
        metadata = {
            "FIC-4001": {"normalized_equipment": "flow_controller", "normalized_type": "controller"},
            "TK-9": {"normalized_equipment": "tank", "normalized_type": "tank"},
        }

        loops, warnings = strict_control_loop_engine.discover(
            entities=entities,
            relationships=relationships,
            metadata_by_entity=metadata,
            intents=[],
        )

        self.assertEqual(loops, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("sensor_not_linked_to_process", warnings[0])

    def test_deduplicates_by_sensor_actuator_process_and_sorts_by_confidence(self) -> None:
        entities = [
            EngineeringEntity(id="FIT-1001", tag="FIT-1001", canonical_type="flow_transmitter", display_name="FIT-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="FIC-1001", tag="FIC-1001", canonical_type="panel", display_name="FIC-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="FCV-1001", tag="FCV-1001", canonical_type="control_valve", display_name="FCV-1001", process_unit="BASIN-1"),
            EngineeringEntity(id="PIT-2201", tag="PIT-2201", canonical_type="pressure_transmitter", display_name="PIT-2201", process_unit="REACTOR-1"),
            EngineeringEntity(id="PCV-2201", tag="PCV-2201", canonical_type="control_valve", display_name="PCV-2201", process_unit="REACTOR-1"),
            EngineeringEntity(id="BASIN-1", tag="BASIN-1", canonical_type="basin", display_name="Basin 1", process_unit="BASIN-1", is_synthetic=True),
            EngineeringEntity(id="REACTOR-1", tag="REACTOR-1", canonical_type="reactor", display_name="Reactor 1", process_unit="REACTOR-1", is_synthetic=True),
        ]
        relationships = [
            InferredRelationship(relationship_type="MEASURES", source_entity="FIT-1001", target_entity="BASIN-1", confidence_score=0.9, confidence_level="HIGH", inference_source="narrative", explanation="", source_references=["narrative:p1"]),
            InferredRelationship(relationship_type="SIGNAL_TO", source_entity="FIT-1001", target_entity="FIC-1001", confidence_score=0.89, confidence_level="HIGH", inference_source="narrative", explanation="", source_references=["narrative:p1"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="FIC-1001", target_entity="FCV-1001", confidence_score=0.9, confidence_level="HIGH", inference_source="narrative", explanation="", source_references=["narrative:p1"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="FIT-1001", target_entity="FCV-1001", confidence_score=0.76, confidence_level="MEDIUM", inference_source="merged", explanation="", source_references=["pid:p1"]),
            InferredRelationship(relationship_type="PART_OF", source_entity="FCV-1001", target_entity="BASIN-1", confidence_score=0.84, confidence_level="HIGH", inference_source="assignment", explanation="", source_references=["pid:p1"]),
            InferredRelationship(relationship_type="MEASURES", source_entity="PIT-2201", target_entity="REACTOR-1", confidence_score=0.82, confidence_level="HIGH", inference_source="merged", explanation="", source_references=["pid:p2"]),
            InferredRelationship(relationship_type="CONTROLS", source_entity="PIT-2201", target_entity="PCV-2201", confidence_score=0.79, confidence_level="MEDIUM", inference_source="merged", explanation="", source_references=["pid:p2"]),
            InferredRelationship(relationship_type="PART_OF", source_entity="PCV-2201", target_entity="REACTOR-1", confidence_score=0.8, confidence_level="MEDIUM", inference_source="assignment", explanation="", source_references=["pid:p2"]),
        ]
        metadata = {
            "FIC-1001": {"normalized_equipment": "pid_controller", "normalized_type": "controller"},
            "BASIN-1": {"normalized_equipment": "basin", "normalized_type": "basin"},
            "REACTOR-1": {"normalized_equipment": "reactor", "normalized_type": "reactor"},
        }

        loops, warnings = strict_control_loop_engine.discover(
            entities=entities,
            relationships=relationships,
            metadata_by_entity=metadata,
            intents=[],
        )

        self.assertEqual(warnings, [])
        self.assertEqual(len(loops), 2)
        self.assertEqual((loops[0].sensor_tag, loops[0].actuator_tag, loops[0].process_node), ("FIT-1001", "FCV-1001", "BASIN-1"))
        self.assertEqual((loops[1].sensor_tag, loops[1].actuator_tag, loops[1].process_node), ("PIT-2201", "PCV-2201", "REACTOR-1"))
        self.assertGreaterEqual(loops[0].confidence, loops[1].confidence)


if __name__ == "__main__":
    unittest.main()