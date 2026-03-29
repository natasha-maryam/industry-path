import unittest

from models.document_pipeline import PipelineControlLoopRecord, SegmentedDocumentBlock
from services.validation_control_loop_layer import validation_control_loop_layer


class ValidationControlLoopTuningTests(unittest.TestCase):
    def test_detects_pid_parameters_mode_and_behavior_terms_from_narrative(self) -> None:
        loop = PipelineControlLoopRecord(
            loop_id="loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1",
            name="FIT-1001 -> FIC-1001 -> FCV-1001 -> BASIN-1",
            sensor_tag="FIT-1001",
            controller_tag="FIC-1001",
            actuator_tag="FCV-1001",
            process_node="BASIN-1",
            chain=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
            source_texts=["narrative.pdf:p4:narrative_section:1"],
            confidence=0.93,
            tuning_confidence=0.0,
        )
        structured = type(
            "Structured",
            (),
            {
                "blocks": [
                    SegmentedDocumentBlock(
                        section_id="sec-1",
                        block_id="block-1",
                        file_id="doc-1",
                        file_name="narrative.pdf",
                        document_id="doc-1",
                        document_type="control_narrative",
                        kind="narrative",
                        page=4,
                        page_number=4,
                        block_type="narrative_section",
                        text="Loop FIT-1001 to FCV-1001 tuned in auto mode. Kp=1.2 Ki=0.4 Kd=0.05 reset time=6 proportional band=18. Response was unstable with overshoot and oscillation.",
                        source_references=["narrative.pdf:p4:narrative_section:1"],
                    )
                ]
            },
        )()

        tuning_data, warnings = validation_control_loop_layer._detect_tuning_data(structured, [loop])
        merged = validation_control_loop_layer._apply_tuning_data([loop], tuning_data)

        self.assertEqual(warnings, [])
        self.assertEqual(len(tuning_data), 1)
        self.assertEqual(tuning_data[0].loop_reference, loop.loop_id)
        self.assertEqual(tuning_data[0].mode, "auto")
        self.assertEqual(tuning_data[0].behavior_terms, ["oscillation", "overshoot", "unstable"])
        self.assertEqual(tuning_data[0].kp, 1.2)
        self.assertEqual(tuning_data[0].ki, 0.4)
        self.assertEqual(tuning_data[0].kd, 0.05)
        self.assertEqual(tuning_data[0].reset_time, 6.0)
        self.assertEqual(tuning_data[0].proportional_band, 18.0)
        self.assertGreater(merged[0].tuning_confidence, 0.6)
        self.assertEqual(merged[0].tuning.get("mode"), "auto")
        self.assertIn("narrative.pdf:p4:narrative_section:1", merged[0].tuning.get("source_references", []))

    def test_associates_table_tuning_to_nearest_control_context_by_proximity(self) -> None:
        loop_a = PipelineControlLoopRecord(
            loop_id="loop:PIT-2201:CTRL_2201:PCV-2201:REACTOR-1",
            name="PIT-2201 -> CTRL_2201 -> PCV-2201 -> REACTOR-1",
            sensor_tag="PIT-2201",
            controller_tag="CTRL_2201",
            actuator_tag="PCV-2201",
            process_node="REACTOR-1",
            chain=["PIT-2201", "CTRL_2201", "PCV-2201", "REACTOR-1"],
            source_texts=["pid.pdf:p2:table:1"],
            confidence=0.88,
            tuning_confidence=0.0,
        )
        loop_b = PipelineControlLoopRecord(
            loop_id="loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1",
            name="FIT-1001 -> FIC-1001 -> FCV-1001 -> BASIN-1",
            sensor_tag="FIT-1001",
            controller_tag="FIC-1001",
            actuator_tag="FCV-1001",
            process_node="BASIN-1",
            chain=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
            source_texts=["narrative.pdf:p8:narrative_section:1"],
            confidence=0.9,
            tuning_confidence=0.0,
        )
        structured = type(
            "Structured",
            (),
            {
                "blocks": [
                    SegmentedDocumentBlock(
                        section_id="sec-2",
                        block_id="block-2",
                        file_id="doc-2",
                        file_name="pid.pdf",
                        document_id="doc-2",
                        document_type="pid_pdf",
                        kind="table",
                        page=2,
                        page_number=2,
                        block_type="table",
                        text="Controller settings",
                        table_rows=[["PIT-2201", "PCV-2201", "Ki=0.6", "manual", "hunting noisy response"]],
                        source_references=["pid.pdf:p2:table:1"],
                    )
                ]
            },
        )()

        tuning_data, warnings = validation_control_loop_layer._detect_tuning_data(structured, [loop_b, loop_a])
        merged = validation_control_loop_layer._apply_tuning_data([loop_b, loop_a], tuning_data)

        self.assertEqual(warnings, [])
        self.assertEqual(len(tuning_data), 1)
        self.assertEqual(tuning_data[0].loop_reference, loop_a.loop_id)
        self.assertEqual(tuning_data[0].mode, "manual")
        self.assertEqual(tuning_data[0].behavior_terms, ["hunting", "noisy_response"])
        merged_loop = next(item for item in merged if item.loop_id == loop_a.loop_id)
        self.assertEqual(merged_loop.tuning.get("ki"), 0.6)
        self.assertIn("manual", str(merged_loop.tuning.get("mode")))


if __name__ == "__main__":
    unittest.main()