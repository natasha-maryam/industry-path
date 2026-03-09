import unittest

from models.pipeline import (
    AlarmDefinition,
    ControlLoopDefinition,
    EngineeringEntity,
    InterlockDefinition,
)
from services.relationship_inference_service import relationship_inference_service


class RelationshipInferenceTests(unittest.TestCase):
    def test_narrative_controls_relationship_is_high_confidence(self) -> None:
        entities = [
            EngineeringEntity(
                id="AIT-2301",
                tag="AIT-2301",
                canonical_type="analyzer",
                display_name="AIT-2301",
                process_unit="aeration_basin",
            ),
            EngineeringEntity(
                id="FCV-2301",
                tag="FCV-2301",
                canonical_type="control_valve",
                display_name="FCV-2301",
                process_unit="aeration_basin",
            ),
        ]
        rules = {
            "control_loops": [
                ControlLoopDefinition(
                    name="DO analyzer controls valve",
                    source_sentence="Dissolved oxygen analyzer AIT-2301 controls FCV-2301.",
                    page_number=2,
                    related_tags=["AIT-2301", "FCV-2301"],
                    confidence=0.95,
                )
            ],
            "alarms": [
                AlarmDefinition(
                    name="High alarm",
                    source_sentence="High level alarm LSHH-2001.",
                    page_number=3,
                    related_tags=["LSHH-2001"],
                    confidence=0.8,
                )
            ],
            "interlocks": [
                InterlockDefinition(
                    name="Pump trip interlock",
                    source_sentence="PMP-2601 interlocks with XV-2001.",
                    page_number=4,
                    related_tags=["PMP-2601", "XV-2001"],
                    confidence=0.85,
                )
            ],
            "sequences": [],
            "modes": [],
        }

        high_medium, low, warnings = relationship_inference_service.infer(entities, rules, pid_chunks=[])

        self.assertTrue(any(item.relationship_type == "CONTROLS" for item in high_medium))
        controls = [item for item in high_medium if item.relationship_type == "CONTROLS"]
        self.assertTrue(any(item.confidence_level == "HIGH" for item in controls))
        self.assertEqual(warnings, [])
        self.assertIsInstance(low, list)


if __name__ == "__main__":
    unittest.main()
