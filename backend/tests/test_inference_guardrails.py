import unittest

from models.pipeline import EngineeringEntity
from services.relationship_inference_service import relationship_inference_service


class InferenceGuardrailTests(unittest.TestCase):
    def test_no_instrument_to_instrument_heuristic_edges(self) -> None:
        entities = [
            EngineeringEntity(
                id="LIT-2001",
                tag="LIT-2001",
                canonical_type="level_transmitter",
                display_name="LIT-2001",
                process_unit="influent_pump_station",
                source_pages=[1],
            ),
            EngineeringEntity(
                id="FIT-2301",
                tag="FIT-2301",
                canonical_type="flow_transmitter",
                display_name="FIT-2301",
                process_unit="influent_pump_station",
                source_pages=[1],
            ),
            EngineeringEntity(
                id="PMP-2601",
                tag="PMP-2601",
                canonical_type="pump",
                display_name="PMP-2601",
                process_unit="influent_pump_station",
                source_pages=[1],
            ),
        ]

        rules = {"control_loops": [], "alarms": [], "interlocks": [], "sequences": [], "modes": []}
        high_medium, _, _ = relationship_inference_service.infer(entities, rules, pid_chunks=[])

        bad_edges = [
            item
            for item in high_medium
            if item.source_entity in {"LIT-2001", "FIT-2301"} and item.target_entity in {"LIT-2001", "FIT-2301"}
        ]
        self.assertEqual(bad_edges, [])


if __name__ == "__main__":
    unittest.main()
