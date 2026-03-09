import unittest

from services.control_rule_normalization_service import control_rule_normalization_service
from services.control_rule_extraction_service import ExtractedRuleDraft


class ControlRuleRenderingGuardTests(unittest.TestCase):
    def test_rejects_process_unit_as_condition_source(self) -> None:
        drafts = [
            ExtractedRuleDraft(
                rule_group="aeration",
                rule_type="modulate",
                source_tag="AERATION-BASIN-AREA",
                source_type="process_unit",
                condition_kind="analyzer",
                operator="<",
                threshold="DO_SETPOINT",
                threshold_name="DO_SETPOINT",
                action="MODULATE",
                target_tag="FCV-2301",
                target_type="control_valve",
                secondary_target_tag=None,
                mode="AUTO",
                priority=10,
                confidence=0.8,
                source_sentence="AERATION-BASIN-AREA controls FCV-2301",
                source_page=2,
                section_heading="aeration",
                explanation="bad placeholder case",
                renderable=True,
                unresolved_tokens=[],
                comments=[],
                source_references=["test"],
            )
        ]

        rules = control_rule_normalization_service.normalize("p1", drafts)
        self.assertFalse(rules[0].renderable)
        self.assertIn("TODO", rules[0].st_preview)
        self.assertNotIn("IF TRUE", rules[0].st_preview)


if __name__ == "__main__":
    unittest.main()
