import unittest
from types import SimpleNamespace

from models.document_pipeline import (
    PipelineControlLoopRecord,
    TuningDataRecord,
    ValidatedGraphRecord,
    ValidationControlLoopLayerResult,
)
from models.pipeline import EngineeringEntity, InferredRelationship
from services.final_validation_service import final_validation_service


class FinalValidationServiceTests(unittest.TestCase):
    def test_rejects_invalid_rows_and_conflicting_relationships_before_final_output(self) -> None:
        structured = SimpleNamespace(extracted_relationships=[])
        semantic = SimpleNamespace(
            entities=[
                EngineeringEntity(id="FIT-1001", tag="FIT-1001", canonical_type="flow_transmitter", display_name="FIT-1001", process_unit="BASIN-1", confidence=0.92),
                EngineeringEntity(id="FIC-1001", tag="FIC-1001", canonical_type="panel", display_name="FIC-1001", process_unit="BASIN-1", confidence=0.9),
                EngineeringEntity(id="FCV-1001", tag="FCV-1001", canonical_type="control_valve", display_name="FCV-1001", process_unit="BASIN-1", confidence=0.9),
                EngineeringEntity(id="BASIN-1", tag="BASIN-1", canonical_type="basin", display_name="Basin 1", process_unit="BASIN-1", confidence=0.95, is_synthetic=True),
                EngineeringEntity(id="BAD-1", tag="BAD-1", canonical_type="generic_device", display_name="Bad Device", process_unit="BASIN-1", confidence=0.8),
                EngineeringEntity(id="AIT-5001", tag="AIT-5001", canonical_type="analyzer", display_name="AIT-5001", process_unit="BASIN-1", confidence=0.85),
            ],
            metadata_by_entity={
                "FIT-1001": {"normalized_type": "flow_transmitter", "equipment_type": "flow_transmitter"},
                "FIC-1001": {"normalized_type": "panel", "equipment_type": "pid_controller"},
                "FCV-1001": {"normalized_type": "control_valve", "equipment_type": "control_valve"},
                "BASIN-1": {"normalized_type": "basin", "equipment_type": "aeration_basin"},
                "BAD-1": {"normalized_type": "generic_device", "equipment_type": "generic_equipment"},
                "AIT-5001": {"normalized_type": "analyzer", "equipment_type": "analyzer"},
            },
            behavioral_chains=[],
        )
        validated_relationships = [
            InferredRelationship(
                relationship_type="MEASURES",
                source_entity="FIT-1001",
                target_entity="BASIN-1",
                confidence_score=0.91,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIT-1001 measures BASIN-1.",
                source_references=["narrative:p1"],
            ),
            InferredRelationship(
                relationship_type="SIGNAL_TO",
                source_entity="FIT-1001",
                target_entity="FIC-1001",
                confidence_score=0.89,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIT-1001 signals FIC-1001.",
                source_references=["narrative:p1"],
            ),
            InferredRelationship(
                relationship_type="SIGNAL_TO",
                source_entity="FIT-1001",
                target_entity="FIC-1001",
                confidence_score=0.76,
                confidence_level="MEDIUM",
                inference_source="merged",
                explanation="Duplicate weaker signal edge.",
                source_references=["pid:p2"],
            ),
            InferredRelationship(
                relationship_type="CONTROLS",
                source_entity="FIC-1001",
                target_entity="FCV-1001",
                confidence_score=0.9,
                confidence_level="HIGH",
                inference_source="narrative",
                explanation="FIC-1001 controls FCV-1001.",
                source_references=["narrative:p1"],
            ),
            InferredRelationship(
                relationship_type="PART_OF",
                source_entity="FCV-1001",
                target_entity="BASIN-1",
                confidence_score=0.87,
                confidence_level="HIGH",
                inference_source="assignment",
                explanation="FCV-1001 belongs to BASIN-1.",
                source_references=["pid:p2"],
            ),
            InferredRelationship(
                relationship_type="MEASURES",
                source_entity="BASIN-1",
                target_entity="FIT-1001",
                confidence_score=0.71,
                confidence_level="MEDIUM",
                inference_source="merged",
                explanation="Contradictory reverse measurement.",
                source_references=["pid:p2"],
            ),
            InferredRelationship(
                relationship_type="CONTROLS",
                source_entity="BAD-1",
                target_entity="FCV-1001",
                confidence_score=0.79,
                confidence_level="MEDIUM",
                inference_source="heuristic",
                explanation="Bad device controls FCV-1001.",
                source_references=["ocr:p3"],
            ),
        ]
        validation = ValidationControlLoopLayerResult(
            validated_graph=ValidatedGraphRecord(
                entities=list(semantic.entities),
                relationships=validated_relationships,
                rejected_relationships=[],
            ),
            control_loops=[
                PipelineControlLoopRecord(
                    loop_id="loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1",
                    name="FIT-1001 -> FIC-1001 -> FCV-1001 -> BASIN-1",
                    sensor_tag="FIT-1001",
                    controller_tag="FIC-1001",
                    actuator_tag="FCV-1001",
                    process_node="BASIN-1",
                    chain=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
                    confidence=0.94,
                    validation_score=0.94,
                    continuity_score=0.93,
                ),
                PipelineControlLoopRecord(
                    loop_id="loop:BAD-1:FCV-1001:BASIN-1",
                    name="BAD-1 -> FCV-1001 -> BASIN-1",
                    sensor_tag="BAD-1",
                    actuator_tag="FCV-1001",
                    process_node="BASIN-1",
                    chain=["BAD-1", "FCV-1001"],
                    confidence=0.66,
                    validation_score=0.52,
                    continuity_score=0.48,
                ),
            ],
            rejected_control_loops=[],
            tuning_data=[
                TuningDataRecord(
                    tuning_id="tuning:1",
                    loop_reference="loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1",
                    controller_tag="FIC-1001",
                    kp=1.1,
                    ki=0.3,
                    kd=0.04,
                    source_block_id="block-1",
                    source_page=1,
                    source_text="Kp=1.1 Ki=0.3 Kd=0.04",
                    confidence=0.91,
                ),
                TuningDataRecord(
                    tuning_id="tuning:2",
                    loop_reference="loop:BAD-1:FCV-1001:BASIN-1",
                    controller_tag=None,
                    kp=9.9,
                    source_block_id="block-2",
                    source_page=2,
                    source_text="Bad tuning",
                    confidence=0.4,
                ),
            ],
            low_confidence_relationships=[
                InferredRelationship(
                    relationship_type="CONTROLS",
                    source_entity="AIT-5001",
                    target_entity="FCV-1001",
                    confidence_score=0.42,
                    confidence_level="LOW",
                    inference_source="heuristic",
                    explanation="Low confidence relationship.",
                    source_references=["ocr:p4"],
                )
            ],
        )

        result = final_validation_service.process(structured, semantic, validation)

        self.assertEqual([row.tag for row in result.tag_rows], ["BASIN-1", "FCV-1001", "FIC-1001", "FIT-1001"])
        self.assertEqual(sorted(row.tag for row in result.rejected_tag_rows), ["AIT-5001", "BAD-1"])
        self.assertEqual(
            [(item.source_entity, item.target_entity, item.relationship_type) for item in result.validated_graph.relationships],
            [
                ("FCV-1001", "BASIN-1", "PART_OF"),
                ("FIC-1001", "FCV-1001", "CONTROLS"),
                ("FIT-1001", "BASIN-1", "MEASURES"),
                ("FIT-1001", "FIC-1001", "SIGNAL_TO"),
            ],
        )
        self.assertEqual([item.loop_id for item in result.control_loops], ["loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1"])
        self.assertEqual(len(result.rejected_control_loops), 1)
        self.assertEqual([item.tuning_id for item in result.tuning_data], ["tuning:1"])
        self.assertEqual(result.diagnostics.total_tags, 6)
        self.assertEqual(result.diagnostics.rejected_tags, 2)
        self.assertEqual(result.diagnostics.total_relationships, 8)
        self.assertEqual(result.diagnostics.rejected_relationships, 4)
        self.assertEqual(result.diagnostics.total_loops, 2)
        self.assertEqual(result.diagnostics.rejected_loops, 1)
        self.assertEqual(result.diagnostics.duplicate_edges_removed, 1)
        self.assertEqual(result.diagnostics.duplicate_loops_removed, 0)
        self.assertGreater(result.diagnostics.inferred_links, 0)
        self.assertEqual(result.validated_graph.parser_graph.contradictions, [])


if __name__ == "__main__":
    unittest.main()