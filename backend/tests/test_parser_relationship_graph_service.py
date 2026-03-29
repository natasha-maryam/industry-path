import unittest

from models.document_pipeline import IntermediateEdgeCandidate, IntermediateNodeCandidate
from services.parser_relationship_graph_service import parser_relationship_graph_service


class ParserRelationshipGraphServiceTests(unittest.TestCase):
    def test_builds_deduplicated_graph_with_evidence_and_flow_adjacency(self) -> None:
        nodes = [
            IntermediateNodeCandidate(candidate_id="node:FIT-1001", normalized_tag="FIT-1001", canonical_type="flow_transmitter", normalized_equipment="flow_transmitter", normalized_type="flow_transmitter", display_name="FIT-1001", confidence=0.9),
            IntermediateNodeCandidate(candidate_id="node:FCV-1001", normalized_tag="FCV-1001", canonical_type="control_valve", normalized_equipment="flow_control_valve", normalized_type="control_valve", display_name="FCV-1001", confidence=0.9),
            IntermediateNodeCandidate(candidate_id="node:PMP-1001", normalized_tag="PMP-1001", canonical_type="pump", normalized_equipment="pump", normalized_type="pump", display_name="PMP-1001", confidence=0.9),
            IntermediateNodeCandidate(candidate_id="node:TK-1001", normalized_tag="TK-1001", canonical_type="tank", normalized_equipment="tank", normalized_type="tank", display_name="TK-1001", confidence=0.9),
        ]
        edges = [
            IntermediateEdgeCandidate(
                candidate_id="edge:1",
                relationship_type="CONTROLS",
                source_tag="FIT-1001",
                target_tag="FCV-1001",
                raw_relationship_types=["CONTROLS"],
                source_section_references=["doc:p1:s1"],
                source_pages=[1],
                source_texts=["FIT-1001 controls FCV-1001"],
                raw_verbs=["controls"],
                confidence=0.9,
                confidence_metadata={"sources": [{"method": "verb", "confidence": 0.9}]},
            ),
            IntermediateEdgeCandidate(
                candidate_id="edge:2",
                relationship_type="CONTROLS",
                source_tag="FIT-1001",
                target_tag="FCV-1001",
                raw_relationship_types=["CONTROLS"],
                source_section_references=["doc:p2:s4"],
                source_pages=[2],
                source_texts=["FIT-1001 maintains flow through FCV-1001"],
                raw_verbs=["maintains"],
                related_intent_types=["flow_control"],
                confidence=0.86,
                confidence_metadata={"sources": [{"method": "intent", "confidence": 0.86}]},
            ),
            IntermediateEdgeCandidate(
                candidate_id="edge:3",
                relationship_type="FEEDS",
                source_tag="PMP-1001",
                target_tag="TK-1001",
                raw_relationship_types=["FEEDS"],
                source_section_references=["pid:p3:z1"],
                source_pages=[3],
                source_texts=["PMP-1001 feeds TK-1001"],
                raw_verbs=["feeds"],
                confidence=0.84,
                confidence_metadata={"sources": [{"method": "verb", "confidence": 0.84}]},
            ),
        ]

        graph = parser_relationship_graph_service.build(nodes, edges)

        self.assertEqual(len(graph.nodes), 4)
        self.assertEqual(len(graph.edges), 2)
        control_edge = next(edge for edge in graph.edges if edge.relationship_type == "control")
        flow_edge = next(edge for edge in graph.edges if edge.relationship_type == "flow")
        self.assertEqual(control_edge.evidence_references, ["doc:p1:s1", "doc:p2:s4"])
        self.assertEqual(sorted(control_edge.raw_verbs), ["controls", "maintains"])
        self.assertGreaterEqual(control_edge.confidence_factors.direct_textual_evidence, 0.6)
        self.assertEqual(graph.outgoing_adjacency["PMP-1001"], ["TK-1001"])
        self.assertEqual(graph.downstream_map["PMP-1001"], ["TK-1001"])
        self.assertEqual(graph.upstream_map["TK-1001"], ["PMP-1001"])
        self.assertGreaterEqual(flow_edge.confidence_score, 0.84)
        self.assertGreater(flow_edge.confidence_factors.topology_consistency, 0.8)

    def test_detects_contradictory_bidirectional_flow_relationships(self) -> None:
        nodes = [
            IntermediateNodeCandidate(candidate_id="node:PMP-1", normalized_tag="PMP-1", canonical_type="pump", normalized_equipment="pump", normalized_type="pump", display_name="PMP-1"),
            IntermediateNodeCandidate(candidate_id="node:TK-1", normalized_tag="TK-1", canonical_type="tank", normalized_equipment="tank", normalized_type="tank", display_name="TK-1"),
        ]
        edges = [
            IntermediateEdgeCandidate(candidate_id="edge:1", relationship_type="FEEDS", source_tag="PMP-1", target_tag="TK-1", raw_relationship_types=["FEEDS"], source_section_references=["a"], confidence_metadata={"sources": [{"method": "verb"}]}, confidence=0.8),
            IntermediateEdgeCandidate(candidate_id="edge:2", relationship_type="FEEDS", source_tag="TK-1", target_tag="PMP-1", raw_relationship_types=["FEEDS"], source_section_references=["b"], confidence_metadata={"sources": [{"method": "verb"}]}, confidence=0.8),
        ]

        graph = parser_relationship_graph_service.build(nodes, edges)

        self.assertEqual(len(graph.contradictions), 2)
        self.assertTrue(all(item.contradiction_type == "bidirectional_relationship" for item in graph.contradictions))


if __name__ == "__main__":
    unittest.main()