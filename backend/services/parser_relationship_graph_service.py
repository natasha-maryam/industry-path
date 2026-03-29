from __future__ import annotations

from collections import defaultdict, deque
import re

from models.document_pipeline import (
    IntermediateEdgeCandidate,
    IntermediateNodeCandidate,
    ParserGraphContradiction,
    ParserGraphEdge,
    ParserGraphEdgeConfidence,
    ParserGraphEvidence,
    ParserGraphNode,
    ParserRelationshipGraph,
)
from models.pipeline import EngineeringEntity, InferredRelationship


class ParserRelationshipGraphService:
    SENSOR_TYPES = {
        "analyzer",
        "flow_transmitter",
        "level_transmitter",
        "level_switch",
        "pressure_transmitter",
        "differential_pressure_transmitter",
        "temperature_transmitter",
    }
    ACTUATOR_TYPES = {"pump", "valve", "control_valve", "blower", "motor", "vfd"}
    PROCESS_TYPES = {"tank", "basin", "clarifier", "reactor", "filter", "heat_exchanger", "boiler", "cooler", "pipe", "manifold", "process_unit"}

    def build(self, node_candidates: list[IntermediateNodeCandidate], edge_candidates: list[IntermediateEdgeCandidate]) -> ParserRelationshipGraph:
        node_map = {node.normalized_tag: node for node in node_candidates}
        graph_nodes = [
            ParserGraphNode(
                tag=node.normalized_tag,
                canonical_type=node.canonical_type,
                display_name=node.display_name,
                normalized_equipment=node.normalized_equipment,
                normalized_type=node.normalized_type or node.canonical_type,
                confidence=node.confidence,
                evidence_references=list(node.source_section_references),
            )
            for node in sorted(node_candidates, key=lambda item: item.normalized_tag)
        ]

        deduped_edges: dict[tuple[str, str, str], ParserGraphEdge] = {}
        for candidate in edge_candidates:
            relationship_type = self._graph_relationship_type(candidate.relationship_type)
            if relationship_type is None:
                continue
            key = (candidate.source_tag, candidate.target_tag, relationship_type)
            evidence = self._edge_evidence(candidate)
            confidence_factors = self._confidence_factors(candidate, node_map, relationship_type)
            confidence_score = self._confidence_score(confidence_factors, candidate.confidence)
            current = deduped_edges.get(key)
            if current is None:
                deduped_edges[key] = ParserGraphEdge(
                    edge_id=f"graph:{candidate.source_tag}:{relationship_type}:{candidate.target_tag}",
                    source=candidate.source_tag,
                    target=candidate.target_tag,
                    relationship_type=relationship_type,
                    raw_relationship_types=sorted(set(candidate.raw_relationship_types or [candidate.relationship_type])),
                    confidence_score=confidence_score,
                    confidence_factors=confidence_factors,
                    evidence_references=list(candidate.source_section_references),
                    evidence=evidence,
                    related_intent_types=list(candidate.related_intent_types),
                    raw_verbs=list(candidate.raw_verbs),
                )
                continue

            current.raw_relationship_types = sorted(set([*current.raw_relationship_types, *(candidate.raw_relationship_types or [candidate.relationship_type])]))
            current.related_intent_types = sorted(set([*current.related_intent_types, *candidate.related_intent_types]))
            current.raw_verbs = sorted(set([*current.raw_verbs, *candidate.raw_verbs]))
            current.evidence_references = sorted(set([*current.evidence_references, *candidate.source_section_references]))
            current.evidence = self._merge_evidence(current.evidence, evidence)
            current.confidence_factors = self._merge_confidence_factors(current.confidence_factors, confidence_factors)
            current.confidence_score = max(current.confidence_score, self._confidence_score(current.confidence_factors, max(current.confidence_score, candidate.confidence)))

        graph_edges = sorted(deduped_edges.values(), key=lambda item: (item.source, item.target, item.relationship_type))
        outgoing_adjacency = self._adjacency_map(graph_edges, direction="outgoing")
        incoming_adjacency = self._adjacency_map(graph_edges, direction="incoming")
        downstream_map = self._reachability_map(graph_edges, direction="downstream")
        upstream_map = self._reachability_map(graph_edges, direction="upstream")
        contradictions = self.find_contradictions(graph_edges)
        warnings = [item.message for item in contradictions]
        return ParserRelationshipGraph(
            nodes=graph_nodes,
            edges=graph_edges,
            outgoing_adjacency=outgoing_adjacency,
            incoming_adjacency=incoming_adjacency,
            downstream_map=downstream_map,
            upstream_map=upstream_map,
            contradictions=contradictions,
            warnings=warnings,
        )

    def build_from_validated_relationships(
        self,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
        metadata_by_entity: dict[str, dict[str, object]] | None = None,
    ) -> ParserRelationshipGraph:
        metadata_by_entity = metadata_by_entity or {}
        node_candidates = [
            IntermediateNodeCandidate(
                candidate_id=f"node:{entity.id}",
                normalized_tag=entity.id,
                canonical_type=entity.canonical_type,
                display_name=entity.display_name,
                normalized_equipment=str(metadata_by_entity.get(entity.id, {}).get("equipment_type") or entity.canonical_type),
                normalized_type=str(metadata_by_entity.get(entity.id, {}).get("normalized_type") or entity.canonical_type),
                source_section_references=list(entity.source_references),
                source_pages=list(entity.source_pages),
                source_texts=list(entity.source_snippets),
                confidence=entity.confidence,
            )
            for entity in entities
        ]
        edge_candidates = [
            IntermediateEdgeCandidate(
                candidate_id=f"edge:{relationship.source_entity}:{relationship.relationship_type}:{relationship.target_entity}",
                relationship_type=relationship.relationship_type,
                source_tag=relationship.source_entity,
                target_tag=relationship.target_entity,
                raw_relationship_types=[relationship.relationship_type],
                source_section_references=list(relationship.source_references),
                source_texts=list(relationship.source_references),
                confidence=relationship.confidence_score,
                confidence_metadata={"sources": [{"method": relationship.inference_source}]},
            )
            for relationship in relationships
        ]
        return self.build(node_candidates, edge_candidates)

    def find_contradictions(self, edges: list[ParserGraphEdge]) -> list[ParserGraphContradiction]:
        contradictions: list[ParserGraphContradiction] = []
        by_pair_type: dict[tuple[str, str, str], ParserGraphEdge] = {(edge.source, edge.target, edge.relationship_type): edge for edge in edges}
        for edge in edges:
            reverse = by_pair_type.get((edge.target, edge.source, edge.relationship_type))
            if reverse is not None and reverse.edge_id != edge.edge_id and edge.relationship_type in {"flow", "control", "measurement"}:
                contradictions.append(
                    ParserGraphContradiction(
                        contradiction_type="bidirectional_relationship",
                        source=edge.source,
                        target=edge.target,
                        relationship_type=edge.relationship_type,
                        edge_ids=sorted({edge.edge_id, reverse.edge_id}),
                        message=f"Detected contradictory {edge.relationship_type} edges between {edge.source} and {edge.target}.",
                    )
                )

        categories_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
        edge_ids_by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
        for edge in edges:
            pair = (edge.source, edge.target)
            categories_by_pair[pair].add(edge.relationship_type)
            edge_ids_by_pair[pair].append(edge.edge_id)
        for pair, categories in categories_by_pair.items():
            if len(categories) > 1:
                contradictions.append(
                    ParserGraphContradiction(
                        contradiction_type="mixed_relationship_categories",
                        source=pair[0],
                        target=pair[1],
                        relationship_type=sorted(categories)[0],
                        edge_ids=sorted(set(edge_ids_by_pair[pair])),
                        message=f"Detected multiple relationship categories between {pair[0]} and {pair[1]}: {', '.join(sorted(categories))}.",
                    )
                )
        unique: dict[tuple[str, str, str, str], ParserGraphContradiction] = {}
        for item in contradictions:
            key = (item.contradiction_type, item.source, item.target, item.relationship_type)
            unique[key] = item
        return sorted(unique.values(), key=lambda item: (item.source, item.target, item.contradiction_type, item.relationship_type))

    def _edge_evidence(self, candidate: IntermediateEdgeCandidate) -> list[ParserGraphEvidence]:
        sources = candidate.confidence_metadata.get("sources", []) if isinstance(candidate.confidence_metadata, dict) else []
        evidence: list[ParserGraphEvidence] = []
        for index, reference in enumerate(candidate.source_section_references):
            source_metadata = sources[index] if index < len(sources) and isinstance(sources[index], dict) else {}
            evidence.append(
                ParserGraphEvidence(
                    reference=reference,
                    source_page=candidate.source_pages[index] if index < len(candidate.source_pages) else None,
                    source_text=candidate.source_texts[index] if index < len(candidate.source_texts) else None,
                    method=str(source_metadata.get("method")) if source_metadata.get("method") is not None else None,
                    raw_verb=(candidate.raw_verbs[index] if index < len(candidate.raw_verbs) else None),
                    confidence=float(source_metadata.get("confidence")) if isinstance(source_metadata.get("confidence"), (int, float)) else None,
                )
            )
        return evidence

    def _confidence_factors(
        self,
        candidate: IntermediateEdgeCandidate,
        node_map: dict[str, IntermediateNodeCandidate],
        relationship_type: str,
    ) -> ParserGraphEdgeConfidence:
        direct = min(0.99, 0.48 + (0.14 * len(set(candidate.source_section_references))) + (0.06 * len(set(candidate.source_texts)))) if candidate.source_section_references else 0.3
        methods = []
        if isinstance(candidate.confidence_metadata, dict):
            for source in candidate.confidence_metadata.get("sources", []):
                if isinstance(source, dict) and source.get("method"):
                    methods.append(str(source["method"]))
        if candidate.raw_verbs or "verb" in methods:
            verb_strength = 0.95
        elif candidate.related_intent_types:
            verb_strength = 0.8
        elif "tag_pattern" in methods:
            verb_strength = 0.52
        else:
            verb_strength = 0.4
        tag_pattern = self._tag_pattern_compatibility(candidate.source_tag, candidate.target_tag, relationship_type)
        topology = self._topology_consistency(node_map.get(candidate.source_tag), node_map.get(candidate.target_tag), relationship_type)
        return ParserGraphEdgeConfidence(
            direct_textual_evidence=round(direct, 3),
            verb_match_strength=round(verb_strength, 3),
            tag_pattern_compatibility=round(tag_pattern, 3),
            topology_consistency=round(topology, 3),
        )

    @staticmethod
    def _confidence_score(factors: ParserGraphEdgeConfidence, base_confidence: float) -> float:
        weighted = (
            (factors.direct_textual_evidence * 0.35)
            + (factors.verb_match_strength * 0.2)
            + (factors.tag_pattern_compatibility * 0.2)
            + (factors.topology_consistency * 0.25)
        )
        return round(min(0.99, max(base_confidence, weighted)), 3)

    @staticmethod
    def _merge_confidence_factors(current: ParserGraphEdgeConfidence, incoming: ParserGraphEdgeConfidence) -> ParserGraphEdgeConfidence:
        return ParserGraphEdgeConfidence(
            direct_textual_evidence=max(current.direct_textual_evidence, incoming.direct_textual_evidence),
            verb_match_strength=max(current.verb_match_strength, incoming.verb_match_strength),
            tag_pattern_compatibility=max(current.tag_pattern_compatibility, incoming.tag_pattern_compatibility),
            topology_consistency=max(current.topology_consistency, incoming.topology_consistency),
        )

    @staticmethod
    def _merge_evidence(current: list[ParserGraphEvidence], incoming: list[ParserGraphEvidence]) -> list[ParserGraphEvidence]:
        merged: dict[tuple[str, int | None, str | None], ParserGraphEvidence] = {}
        for item in [*current, *incoming]:
            merged[(item.reference, item.source_page, item.source_text)] = item
        return sorted(merged.values(), key=lambda item: (item.reference, item.source_page or 0, item.source_text or ""))

    def _topology_consistency(
        self,
        source: IntermediateNodeCandidate | None,
        target: IntermediateNodeCandidate | None,
        relationship_type: str,
    ) -> float:
        if source is None or target is None:
            return 0.55
        source_type = source.normalized_type or source.canonical_type
        target_type = target.normalized_type or target.canonical_type
        if relationship_type == "measurement":
            if source_type in self.SENSOR_TYPES and target_type not in self.SENSOR_TYPES:
                return 0.95
            return 0.35
        if relationship_type == "control":
            if source_type in self.SENSOR_TYPES and (target_type in self.ACTUATOR_TYPES or target_type in self.PROCESS_TYPES):
                return 0.93
            if source_type in self.ACTUATOR_TYPES and target_type in self.PROCESS_TYPES:
                return 0.74
            return 0.4
        if source_type in self.SENSOR_TYPES or target_type in self.SENSOR_TYPES:
            return 0.28
        return 0.9

    def _tag_pattern_compatibility(self, source_tag: str, target_tag: str, relationship_type: str) -> float:
        source_digits = "".join(re.findall(r"\d+", source_tag))
        target_digits = "".join(re.findall(r"\d+", target_tag))
        source_prefix = source_tag.split("-")[0]
        target_prefix = target_tag.split("-")[0]
        same_digits = bool(source_digits and target_digits and source_digits == target_digits)
        if relationship_type == "control":
            if same_digits:
                return 0.95
            if source_prefix[:1] in {"F", "L", "P", "T", "A"} and target_prefix.endswith("CV"):
                return 0.82
            return 0.42
        if relationship_type == "measurement":
            if same_digits:
                return 0.88
            if source_prefix.endswith(("IT", "T", "S")):
                return 0.74
            return 0.4
        if same_digits:
            return 0.8
        if source_prefix != target_prefix:
            return 0.7
        return 0.45

    @staticmethod
    def _graph_relationship_type(relationship_type: str) -> str | None:
        mapping = {
            "PROCESS_FLOW": "flow",
            "CONNECTED_TO": "flow",
            "FEEDS": "flow",
            "DISCHARGES_TO": "flow",
            "SUPPLIES_AIR_TO": "flow",
            "CONTROLS": "control",
            "SIGNAL_TO": "control",
            "INTERLOCKS_WITH": "control",
            "ALARMS_ON": "control",
            "SUPPORTS": "control",
            "MEASURES": "measurement",
            "MONITORS": "measurement",
        }
        return mapping.get(relationship_type)

    @staticmethod
    def _adjacency_map(edges: list[ParserGraphEdge], *, direction: str) -> dict[str, list[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            if direction == "outgoing":
                adjacency[edge.source].add(edge.target)
            else:
                adjacency[edge.target].add(edge.source)
        return {key: sorted(values) for key, values in adjacency.items()}

    def _reachability_map(self, edges: list[ParserGraphEdge], *, direction: str) -> dict[str, list[str]]:
        flow_edges = [edge for edge in edges if edge.relationship_type == "flow"]
        graph: dict[str, set[str]] = defaultdict(set)
        for edge in flow_edges:
            if direction == "downstream":
                graph[edge.source].add(edge.target)
            else:
                graph[edge.target].add(edge.source)

        reachability: dict[str, list[str]] = {}
        for node in sorted(graph):
            seen: set[str] = set()
            queue: deque[str] = deque(sorted(graph[node]))
            ordered: list[str] = []
            while queue:
                current = queue.popleft()
                if current in seen:
                    continue
                seen.add(current)
                ordered.append(current)
                for child in sorted(graph.get(current, set())):
                    if child not in seen:
                        queue.append(child)
            reachability[node] = ordered
        return reachability


parser_relationship_graph_service = ParserRelationshipGraphService()
