import unittest

from services.equipment_normalizer_service import equipment_normalizer_service


class EquipmentNormalizerServiceTests(unittest.TestCase):
    def test_normalizes_common_instrument_and_equipment_tags(self) -> None:
        cases = {
            "FIT-1001": ("flow_transmitter", "flow_transmitter", "tag:FIT"),
            "LIT-1002": ("level_transmitter", "level_transmitter", "tag:LIT"),
            "PIT-1003": ("pressure_transmitter", "pressure_transmitter", "tag:PIT"),
            "TIT-1004": ("temperature_transmitter", "temperature_transmitter", "tag:TIT"),
            "FCV-1005": ("flow_control_valve", "control_valve", "tag:FCV"),
            "PCV-1006": ("pressure_control_valve", "control_valve", "tag:PCV"),
            "PMP-1007": ("pump", "pump", "tag:PMP"),
            "BAS-1008": ("basin", "basin", "tag:BAS"),
        }

        for tag_name, expected in cases.items():
            with self.subTest(tag_name=tag_name):
                result = equipment_normalizer_service.normalize(tag_name=tag_name)
                self.assertEqual(
                    (result.normalized_equipment, result.normalized_type, result.matched_pattern),
                    expected,
                )

    def test_uses_description_phrases_when_tag_family_is_missing(self) -> None:
        result = equipment_normalizer_service.normalize(
            tag_name="ZZ-2001",
            description="The air compressor discharges to the manifold header.",
        )

        self.assertEqual(result.normalized_equipment, "compressor")
        self.assertEqual(result.normalized_type, "compressor")
        self.assertEqual(result.matched_pattern, "phrase:compressor")

    def test_prefers_specific_tag_match_over_generic_fallback(self) -> None:
        result = equipment_normalizer_service.normalize(
            tag_name="PCV-2201",
            description="Pressure control valve on discharge header.",
            fallback_type="valve",
        )

        self.assertEqual(result.normalized_equipment, "pressure_control_valve")
        self.assertEqual(result.normalized_type, "control_valve")
        self.assertEqual(result.matched_pattern, "tag:PCV")


if __name__ == "__main__":
    unittest.main()
