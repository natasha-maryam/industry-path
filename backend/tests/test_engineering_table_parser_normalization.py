import unittest

from models.document_pipeline import BehavioralChainRecord
from models.graph import GraphNode
from services.engineering_table_parser import engineering_table_parser


class EngineeringTableParserNormalizationTests(unittest.TestCase):
    def test_row_building_preserves_normalized_type_and_equipment(self) -> None:
        node = GraphNode(
            id="PCV-2201",
            label="Pressure Control Valve 2201",
            node_type="control_valve",
            normalized_type="control_valve",
            equipment_type="pressure_control_valve",
            process_unit="aeration_basin",
            confidence=0.92,
        )

        entities = engineering_table_parser._entity_extraction([node])
        rows = engineering_table_parser._row_building(
            entities=entities,
            context={"PCV-2201": {"document_source": ["narrative.pdf"], "line_reference": []}},
            relationships={},
            loops={},
            updown={},
            metadata={},
            traceability={},
            derived={"PCV-2201": {"num_connections": 0, "num_upstream": 0, "num_downstream": 0, "control_chain": [], "flow_chain": ["PCV-2201"], "is_orphan": True, "is_controlled": False, "is_actuated": False, "inferred": False}},
            include_inferred=True,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].type, "control_valve")
        self.assertEqual(rows[0].subtype, "control_valve")
        self.assertEqual(rows[0].equipment, "pressure_control_valve")

    def test_upstream_downstream_completion_prefers_topology_before_behavioral_context(self) -> None:
        entities = [
            {
                "tag": "FIT-1001",
                "process_role": "sensor",
                "system": "aeration_basin",
                "is_synthetic": False,
            },
            {
                "tag": "FCV-1001",
                "process_role": "actuator",
                "system": "aeration_basin",
                "is_synthetic": False,
            },
            {
                "tag": "BAS-1001",
                "process_role": "process",
                "system": "aeration_basin",
                "is_synthetic": False,
            },
        ]
        relationships = {
            "FIT-1001": {"controls": {"FCV-1001"}, "measures": {"BAS-1001"}, "connections": {"FCV-1001", "BAS-1001"}},
            "FCV-1001": {"controlled_by": {"FIT-1001"}, "signal_inputs": {"FIT-1001"}, "connections": {"FIT-1001"}},
            "BAS-1001": {"signal_inputs": {"FIT-1001"}, "connections": {"FIT-1001"}},
        }
        loops = {
            "FIT-1001": ["FIT-1001->BAS-1001->FCV-1001"],
            "FCV-1001": ["FIT-1001->BAS-1001->FCV-1001"],
            "BAS-1001": ["FIT-1001->BAS-1001->FCV-1001"],
        }

        updown = engineering_table_parser._upstream_downstream_calculation(
            entities=entities,
            relationships=relationships,
            loops=loops,
            behavioral_chains=[],
            metadata_rows=[],
            max_depth=4,
        )

        self.assertEqual(updown["FIT-1001"]["upstream"], ["BAS-1001"])
        self.assertEqual(updown["FIT-1001"]["downstream"], ["FCV-1001"])
        self.assertTrue(updown["FIT-1001"]["has_inferred_upstream"])
        self.assertEqual(updown["FIT-1001"]["upstream_links"][0].provenance, "inferred_from_topology")

    def test_upstream_downstream_completion_falls_back_to_sentinel_when_isolated(self) -> None:
        entities = [
            {
                "tag": "AIT-9001",
                "process_role": "sensor",
                "system": "clarifier",
                "is_synthetic": False,
            }
        ]

        updown = engineering_table_parser._upstream_downstream_calculation(
            entities=entities,
            relationships={},
            loops={},
            behavioral_chains=[],
            metadata_rows=[],
            max_depth=4,
        )

        self.assertEqual(updown["AIT-9001"]["upstream"], ["system_source:clarifier"])
        self.assertEqual(updown["AIT-9001"]["downstream"], ["system_sink:clarifier"])
        self.assertEqual(updown["AIT-9001"]["upstream_links"][0].provenance, "sentinel_fallback")
        self.assertEqual(updown["AIT-9001"]["downstream_links"][0].provenance, "sentinel_fallback")
        self.assertTrue(updown["AIT-9001"]["has_inferred_upstream"])
        self.assertTrue(updown["AIT-9001"]["has_inferred_downstream"])

    def test_row_building_keeps_non_empty_directional_links_and_provenance(self) -> None:
        node = GraphNode(
            id="AIT-9001",
            label="Analyzer 9001",
            node_type="analyzer",
            normalized_type="analyzer",
            equipment_type="analyzer",
            process_unit="clarifier",
            confidence=0.92,
        )

        entities = engineering_table_parser._entity_extraction([node])
        updown = engineering_table_parser._upstream_downstream_calculation(
            entities=entities,
            relationships={},
            loops={},
            behavioral_chains=[],
            metadata_rows=[],
            max_depth=4,
        )
        rows = engineering_table_parser._row_building(
            entities=entities,
            context={"AIT-9001": {"document_source": ["narrative.pdf"], "line_reference": []}},
            relationships={},
            loops={},
            updown=updown,
            metadata={},
            traceability={},
            derived={"AIT-9001": {"num_connections": 0, "num_upstream": 1, "num_downstream": 1, "control_chain": [], "flow_chain": updown["AIT-9001"]["flow_chain"], "is_orphan": False, "is_controlled": False, "is_actuated": False, "inferred": False}},
            include_inferred=True,
        )

        self.assertEqual(rows[0].upstream, ["system_source:clarifier"])
        self.assertEqual(rows[0].downstream, ["system_sink:clarifier"])
        self.assertEqual(rows[0].upstream_links[0].provenance, "sentinel_fallback")
        self.assertEqual(rows[0].downstream_links[0].provenance, "sentinel_fallback")
        self.assertFalse(rows[0].is_orphan)
        self.assertEqual(rows[0].num_upstream, 1)
        self.assertEqual(rows[0].num_downstream, 1)

    def test_behavioral_chain_metadata_improves_missing_link_inference(self) -> None:
        entities = [
            {
                "tag": "FIT-1001",
                "process_role": "sensor",
                "system": "BASIN-1",
                "is_synthetic": False,
            },
            {
                "tag": "FCV-1001",
                "process_role": "actuator",
                "system": "BASIN-1",
                "is_synthetic": False,
            },
            {
                "tag": "BASIN-1",
                "process_role": "process",
                "system": "BASIN-1",
                "is_synthetic": False,
            },
        ]
        behavioral_chains = [
            BehavioralChainRecord(
                chain_id="chain:FIT-1001:FCV-1001:BASIN-1",
                sensor="FIT-1001",
                actuator="FCV-1001",
                process="BASIN-1",
                chain=["FIT-1001", "FCV-1001", "BASIN-1"],
                evidence=["control_edge:FIT-1001->FCV-1001", "impact_edge:PART_OF:FCV-1001->BASIN-1"],
                support=["graph_topology", "document_text"],
                support_count=2,
                confidence=0.9,
            )
        ]

        updown = engineering_table_parser._upstream_downstream_calculation(
            entities=entities,
            relationships={},
            loops=engineering_table_parser._control_loop_detection(entities, {}, behavioral_chains=behavioral_chains),
            behavioral_chains=behavioral_chains,
            metadata_rows=[],
            max_depth=4,
        )

        self.assertEqual(updown["FCV-1001"]["upstream"], ["FIT-1001"])
        self.assertEqual(updown["FCV-1001"]["downstream"], ["BASIN-1"])
        self.assertEqual(updown["FCV-1001"]["upstream_links"][0].provenance, "inferred_from_behavioral_chain")
        self.assertEqual(updown["BASIN-1"]["upstream"], ["FCV-1001"])
        self.assertEqual(updown["BASIN-1"]["downstream"], ["FIT-1001"])


if __name__ == "__main__":
    unittest.main()