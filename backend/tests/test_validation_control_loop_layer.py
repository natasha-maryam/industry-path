import unittest
from types import SimpleNamespace

from models.document_pipeline import LoopValidationDebugRecord, PipelineControlLoopRecord, ValidationSignalRecord
from models.document_pipeline import NormalizedIntentRecord
from models.pipeline import EngineeringEntity, InferredRelationship
from services.strict_control_loop_engine import strict_control_loop_engine
from services.validation_control_loop_layer import validation_control_loop_layer


class ValidationControlLoopLayerTests(unittest.TestCase):
    def test_detects_loop_from_strict_traversal_engine(self) -> None:
        semantic = SimpleNamespace(
            entities=[
                EngineeringEntity(id="FIT-1001", tag="FIT-1001", canonical_type="flow_transmitter", display_name="FIT-1001", process_unit="BASIN-1"),
                EngineeringEntity(id="FIC-1001", tag="FIC-1001", canonical_type="panel", display_name="FIC-1001", process_unit="BASIN-1"),
                EngineeringEntity(id="FCV-1001", tag="FCV-1001", canonical_type="control_valve", display_name="FCV-1001", process_unit="BASIN-1"),
                EngineeringEntity(id="BASIN-1", tag="BASIN-1", canonical_type="basin", display_name="Basin 1", process_unit="BASIN-1", is_synthetic=True),
            ],
            normalized_intents=[
                NormalizedIntentRecord(
                    intent_id="intent:block-1:1",
                    intent_type="flow_control",
                    normalized_verb="controls",
                    source_tag="FIT-1001",
                    target_tag="FCV-1001",
                    related_tags=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
                    source_text="FIT-1001 sends signal to FIC-1001 which controls FCV-1001.",
                    source_section_id="sec-1",
                    source_section_reference="narrative:p1:s1",
                    source_block_id="block-1",
                    source_file_id="doc-1",
                    source_file_name="narrative.pdf",
                    source_page=1,
                    support=["document_text", "graph_topology", "tag_naming_pattern"],
                    support_count=3,
                    confidence=0.9,
                )
            ],
            metadata_by_entity={
                "FIC-1001": {"normalized_equipment": "pid_controller", "normalized_type": "controller"},
                "BASIN-1": {"normalized_equipment": "aeration_basin", "normalized_type": "basin"},
            },
        )
        validated_relationships = [
            InferredRelationship(
                relationship_type="MEASURES",
                source_entity="FIT-1001",
                target_entity="BASIN-1",
                confidence_score=0.9,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIT-1001 measures basin flow.",
                source_references=["narrative:p1:s1"],
            ),
            InferredRelationship(
                relationship_type="SIGNAL_TO",
                source_entity="FIT-1001",
                target_entity="FIC-1001",
                confidence_score=0.89,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIT-1001 sends signal to FIC-1001.",
                source_references=["narrative:p1:s1"],
            ),
            InferredRelationship(
                relationship_type="CONTROLS",
                source_entity="FIC-1001",
                target_entity="FCV-1001",
                confidence_score=0.9,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIC-1001 controls FCV-1001.",
                source_references=["narrative:p1:s1"],
            ),
            InferredRelationship(
                relationship_type="PART_OF",
                source_entity="FCV-1001",
                target_entity="BASIN-1",
                confidence_score=0.86,
                confidence_level="HIGH",
                inference_source="assignment",
                explanation="FCV-1001 belongs to basin 1.",
                source_references=["process_unit:BASIN-1"],
            ),
        ]

        loops, warnings = strict_control_loop_engine.discover(
            entities=semantic.entities,
            relationships=validated_relationships,
            metadata_by_entity=semantic.metadata_by_entity,
            intents=semantic.normalized_intents,
        )

        self.assertEqual(len(loops), 1)
        self.assertEqual(warnings, [])
        self.assertEqual(loops[0].sensor_tag, "FIT-1001")
        self.assertEqual(loops[0].actuator_tag, "FCV-1001")
        self.assertEqual(loops[0].process_node, "BASIN-1")
        self.assertEqual(loops[0].controller_tag, "FIC-1001")
        self.assertEqual(loops[0].chain, ["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"])
        self.assertGreater(loops[0].confidence, 0.85)

    def test_hides_low_confidence_loops_but_keeps_debug_records(self) -> None:
        visible_loop = PipelineControlLoopRecord(
            loop_id="loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1",
            name="FIT-1001 -> FIC-1001 -> FCV-1001 -> BASIN-1",
            sensor_tag="FIT-1001",
            controller_tag="FIC-1001",
            actuator_tag="FCV-1001",
            process_node="BASIN-1",
            chain=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
            completeness_score=1.0,
            continuity_score=1.0,
            validation_score=1.0,
            relationship_score=0.9,
            confidence=0.95,
            tuning_confidence=0.6,
        )
        hidden_loop = PipelineControlLoopRecord(
            loop_id="loop:PIT-2201:CTRL_2201:PCV-2201:REACTOR-1",
            name="PIT-2201 -> CTRL_2201 -> PCV-2201 -> REACTOR-1",
            sensor_tag="PIT-2201",
            controller_tag="CTRL_2201",
            actuator_tag="PCV-2201",
            process_node="REACTOR-1",
            chain=["PIT-2201", "CTRL_2201", "PCV-2201", "REACTOR-1"],
            completeness_score=0.88,
            continuity_score=0.9,
            validation_score=0.67,
            relationship_score=0.73,
            confidence=0.79,
            tuning_confidence=0.42,
        )
        debug_records = [
            LoopValidationDebugRecord(
                candidate_id=visible_loop.loop_id,
                sensor_tag=visible_loop.sensor_tag,
                actuator_tag=visible_loop.actuator_tag,
                process_node=visible_loop.process_node,
                text_support=ValidationSignalRecord(supported=True, evidence=["narrative:p1"]),
                topology_support=ValidationSignalRecord(supported=True, evidence=["shared_process_unit:BASIN-1"]),
                naming_support=ValidationSignalRecord(supported=True, evidence=["shared_digits:1001"]),
                support_count=3,
                validated=True,
            ),
            LoopValidationDebugRecord(
                candidate_id=hidden_loop.loop_id,
                sensor_tag=hidden_loop.sensor_tag,
                actuator_tag=hidden_loop.actuator_tag,
                process_node=hidden_loop.process_node,
                text_support=ValidationSignalRecord(supported=False, evidence=[]),
                topology_support=ValidationSignalRecord(supported=True, evidence=["shared_process_unit:REACTOR-1"]),
                naming_support=ValidationSignalRecord(supported=True, evidence=["shared_digits:2201"]),
                support_count=2,
                validated=True,
            ),
        ]

        visible, hidden, updated_debug = validation_control_loop_layer._partition_visible_loops(
            [hidden_loop, visible_loop],
            debug_records,
            threshold=0.84,
        )

        self.assertEqual([item.loop_id for item in visible], [visible_loop.loop_id])
        self.assertEqual([item.loop_id for item in hidden], [hidden_loop.loop_id])
        hidden_debug = next(item for item in updated_debug if item.candidate_id == hidden_loop.loop_id)
        self.assertFalse(hidden_debug.visible_by_default)
        self.assertIn("below_visibility_threshold", hidden_debug.rejection_reasons)


if __name__ == "__main__":
    unittest.main()