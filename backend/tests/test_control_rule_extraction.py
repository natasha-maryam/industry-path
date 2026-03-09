import unittest

from models.logic import ControlRuleCandidate
from services.control_rule_extraction_service import control_rule_extraction_service


class ControlRuleExtractionTests(unittest.TestCase):
    def test_extracts_known_tags_and_actions(self) -> None:
        candidates = [
            ControlRuleCandidate(
                id="c1",
                project_id="p1",
                sentence_id="s1",
                rule_type="start_stop",
                source_sentence="If LIT-2001 is high level then start PMP-2001.",
                source_page=5,
                section_heading="influent pump station",
                confidence=0.9,
                reasons=["if-when start/stop clause"],
            )
        ]

        entity_index = {
            "LIT-2001": {
                "id": "LIT-2001",
                "canonical_type": "level_transmitter",
                "display_name": "LIT-2001",
                "aliases": ["LIT-2001"],
            },
            "PMP-2001": {
                "id": "PMP-2001",
                "canonical_type": "pump",
                "display_name": "PMP-2001",
                "aliases": ["PMP-2001", "INFLUENT PUMP"],
            },
        }

        drafts, warnings = control_rule_extraction_service.extract(candidates, entity_index)

        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].source_tag, "LIT-2001")
        self.assertEqual(drafts[0].target_tag, "PMP-2001")
        self.assertEqual(drafts[0].action, "START")
        self.assertEqual(drafts[0].operator, ">")
        self.assertTrue(drafts[0].confidence >= 0.5)
        self.assertIsInstance(warnings, list)

    def test_extracts_analyzer_to_valve_modulation(self) -> None:
        candidates = [
            ControlRuleCandidate(
                id="c2",
                project_id="p1",
                sentence_id="s2",
                rule_type="pid_loop",
                source_sentence="Dissolved oxygen analyzer AIT-2301 controls air valve FCV-2301.",
                source_page=7,
                section_heading="aeration basin",
                rule_group="aeration",
                confidence=0.9,
                reasons=["pid/setpoint marker"],
            )
        ]
        entity_index = {
            "AIT-2301": {
                "id": "AIT-2301",
                "canonical_type": "analyzer",
                "display_name": "AIT-2301",
                "aliases": ["AIT-2301", "DO ANALYZER"],
            },
            "FCV-2301": {
                "id": "FCV-2301",
                "canonical_type": "control_valve",
                "display_name": "FCV-2301",
                "aliases": ["FCV-2301", "AIR VALVE"],
            },
        }

        drafts, _ = control_rule_extraction_service.extract(candidates, entity_index)
        self.assertEqual(drafts[0].source_tag, "AIT-2301")
        self.assertEqual(drafts[0].target_tag, "FCV-2301")
        self.assertEqual(drafts[0].action, "MODULATE")
        self.assertEqual(drafts[0].threshold_name, "DO_SETPOINT")

    def test_extracts_alarm_rule(self) -> None:
        candidates = [
            ControlRuleCandidate(
                id="c3",
                project_id="p1",
                sentence_id="s3",
                rule_type="alarm",
                source_sentence="High-high level alarm generated when LIT-2001 is high-high.",
                source_page=8,
                section_heading="alarms",
                rule_group="alarms",
                confidence=0.86,
                reasons=["alarm phrase"],
            )
        ]
        entity_index = {
            "LIT-2001": {
                "id": "LIT-2001",
                "canonical_type": "level_transmitter",
                "display_name": "LIT-2001",
                "aliases": ["LIT-2001"],
            }
        }
        drafts, _ = control_rule_extraction_service.extract(candidates, entity_index)
        self.assertEqual(drafts[0].action, "ALARM")
        self.assertEqual(drafts[0].source_tag, "LIT-2001")
        self.assertEqual(drafts[0].threshold_name, "HIGH_HIGH")

    def test_marks_weak_lead_lag_trigger_non_renderable(self) -> None:
        candidates = [
            ControlRuleCandidate(
                id="c4",
                project_id="p1",
                sentence_id="s4",
                rule_type="lead_lag",
                source_sentence="Standby blower is selected as lag blower.",
                source_page=10,
                section_heading="blower package",
                rule_group="blower_package",
                confidence=0.8,
                reasons=["lead-lag/standby phrase"],
            )
        ]
        entity_index = {
            "BL-4001": {
                "id": "BL-4001",
                "canonical_type": "blower",
                "display_name": "BL-4001",
                "aliases": ["BL-4001", "STANDBY BLOWER"],
            }
        }

        drafts, _ = control_rule_extraction_service.extract(candidates, entity_index)
        self.assertFalse(drafts[0].renderable)
        self.assertIn("lead_lag_trigger", drafts[0].unresolved_tokens)


if __name__ == "__main__":
    unittest.main()
