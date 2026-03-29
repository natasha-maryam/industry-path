import unittest
from types import SimpleNamespace

from models.document_pipeline import PipelineControlLoopRecord
from models.engineering_table import EngineeringTableRow
from services.parse_service import ParseService


class ParseResponseContractTests(unittest.TestCase):
    def test_final_tag_payloads_include_required_contract_fields(self) -> None:
        row = EngineeringTableRow(
            id="FIT-1001",
            tag="FIT-1001",
            type="flow_transmitter",
            equipment="flow_transmitter",
            upstream=["BASIN-1"],
            downstream=["FCV-1001"],
            confidence=0.91,
            num_connections=2,
            num_upstream=1,
            num_downstream=1,
            is_orphan=False,
            is_controlled=False,
            is_actuated=True,
        )
        pipeline_result = SimpleNamespace(final_validation=SimpleNamespace(tag_rows=[row]))

        payloads = ParseService._final_tag_payloads(pipeline_result)

        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["tag"], "FIT-1001")
        self.assertEqual(payloads[0]["equipment"], "flow_transmitter")
        self.assertEqual(payloads[0]["upstream"], ["BASIN-1"])
        self.assertEqual(payloads[0]["downstream"], ["FCV-1001"])

    def test_final_loop_payloads_include_required_contract_fields(self) -> None:
        loop = PipelineControlLoopRecord(
            loop_id="loop:FIT-1001:FIC-1001:FCV-1001:BASIN-1",
            name="FIT-1001 -> FIC-1001 -> FCV-1001 -> BASIN-1",
            sensor_tag="FIT-1001",
            controller_tag="FIC-1001",
            actuator_tag="FCV-1001",
            process_node="BASIN-1",
            chain=["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"],
            confidence=0.94,
            tuning_confidence=0.63,
        )

        payloads = ParseService._final_loop_payloads([loop])

        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["loop_id"], loop.loop_id)
        self.assertEqual(payloads[0]["sensor"], "FIT-1001")
        self.assertEqual(payloads[0]["actuator"], "FCV-1001")
        self.assertEqual(payloads[0]["process"], "BASIN-1")
        self.assertEqual(payloads[0]["chain"], ["FIT-1001", "FIC-1001", "FCV-1001", "BASIN-1"])
        self.assertEqual(payloads[0]["confidence"], 0.94)
        self.assertEqual(payloads[0]["tuning_confidence"], 0.63)
        self.assertEqual(payloads[0]["controller"], "FIC-1001")
        self.assertEqual(payloads[0]["sensor_tag"], "FIT-1001")


if __name__ == "__main__":
    unittest.main()