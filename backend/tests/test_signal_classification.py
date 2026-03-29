import unittest

from services.signal_classification import classify_behavioral_role


class BehavioralRoleClassificationTests(unittest.TestCase):
    def test_sensor_tag_sets_are_classified_as_sensors(self) -> None:
        for tag in ("FIT-1001", "LIT-1001", "PIT-1001", "TIT-1001"):
            role, evidence, confidence = classify_behavioral_role(tag, node_type="generic_device", normalized_equipment="instrument", normalized_type="generic_device")
            self.assertEqual(role, "sensor")
            self.assertTrue(any(item.startswith("tag_prefix:") for item in evidence))
            self.assertGreaterEqual(confidence, 0.7)

    def test_actuator_candidates_use_tag_patterns_and_equipment_names(self) -> None:
        cases = [
            ("FCV-1001", "control_valve", "control_valve"),
            ("PCV-1001", "pressure_control_valve", "valve"),
            ("P-1001", "pump", "pump"),
            ("BL-1001", "blower", "blower"),
            ("VFD-1001", "variable_frequency_drive", "vfd"),
        ]
        for tag, equipment, node_type in cases:
            role, evidence, confidence = classify_behavioral_role(tag, node_type=node_type, normalized_equipment=equipment, normalized_type=node_type)
            self.assertEqual(role, "actuator")
            self.assertTrue(evidence)
            self.assertGreaterEqual(confidence, 0.78)

    def test_process_candidates_use_normalized_equipment(self) -> None:
        for tag, equipment in (("BASIN-1", "aeration_basin"), ("TK-101", "tank"), ("R-201", "reactor"), ("CLR-1", "clarifier")):
            role, evidence, confidence = classify_behavioral_role(tag, node_type="generic_equipment", normalized_equipment=equipment, normalized_type=equipment)
            self.assertEqual(role, "process")
            self.assertTrue(any("normalized_" in item or item.startswith("canonical_type:") for item in evidence))
            self.assertGreaterEqual(confidence, 0.72)

    def test_controller_candidates_are_classified_from_tags_and_equipment(self) -> None:
        cases = [
            ("FIC-1001", "pid_controller", "panel"),
            ("PIC-2201", "control_panel", "panel"),
            ("CTRL-1", "loop_controller", "generic_device"),
        ]
        for tag, equipment, node_type in cases:
            role, evidence, confidence = classify_behavioral_role(tag, node_type=node_type, normalized_equipment=equipment, normalized_type=equipment)
            self.assertEqual(role, "controller")
            self.assertTrue(evidence)
            self.assertGreaterEqual(confidence, 0.75)


if __name__ == "__main__":
    unittest.main()