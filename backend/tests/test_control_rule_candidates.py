import unittest

from models.logic import NarrativeSentence
from services.control_rule_candidate_service import control_rule_candidate_service


class ControlRuleCandidateTests(unittest.TestCase):
    def test_detects_start_stop_and_alarm_candidates(self) -> None:
        sentences = [
            NarrativeSentence(
                id="s1",
                project_id="p1",
                page_number=5,
                section_heading="influent",
                text="If wet well level is high then start influent pump.",
            ),
            NarrativeSentence(
                id="s2",
                project_id="p1",
                page_number=6,
                section_heading="alarms",
                text="High-high level alarm generated when tank overflows.",
            ),
        ]

        candidates = control_rule_candidate_service.detect("p1", sentences)
        types = [candidate.rule_type for candidate in candidates]

        self.assertIn("start_stop", types)
        self.assertIn("alarm", types)


if __name__ == "__main__":
    unittest.main()
