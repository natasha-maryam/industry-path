from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping


SOURCE_TYPE_WEIGHTS: dict[str, float] = {
    "explicit": 1.0,
    "controls": 0.92,
    "controlled_by": 0.9,
    "signal_inputs": 0.86,
    "signal_outputs": 0.84,
    "upstream": 0.82,
    "downstream": 0.82,
}

RELATION_TYPE_WEIGHTS: dict[str, float] = {
    "CONTROLS": 1.0,
    "REGULATES": 0.96,
    "CONTROLLED_BY": 0.9,
    "SIGNAL": 0.9,
    "SIGNAL_INPUT": 0.88,
    "SIGNAL_OUTPUT": 0.86,
    "UPSTREAM": 0.8,
    "DOWNSTREAM": 0.8,
    "RELATED_TO": 0.72,
}

ROLE_BONUS_WEIGHTS: dict[str, float] = {
    "sensor": 1.06,
    "instrument": 1.06,
    "actuator": 1.04,
    "controller": 1.08,
    "process_unit": 1.05,
    "passive_equipment": 0.96,
    "internal_logical": 0.92,
    "unknown": 0.9,
}


@dataclass(slots=True)
class ChainEdge:
    source: str
    target: str
    rel_type: str
    confidence: float
    source_type: str


@dataclass(slots=True)
class RawPath:
    nodes: list[str]
    edges: list[ChainEdge]
    broken: bool
    break_reason: str
    weak_links: list[dict[str, Any]]
    score: float


class WhyChainResolver:
    def __init__(self) -> None:
        self._default_source_weight = 0.75
        self._default_relation_weight = 0.72
        self._default_role_bonus = ROLE_BONUS_WEIGHTS["unknown"]

    def resolve_ranked_chains(
        self,
        *,
        target_tag: str,
        nodes: Mapping[str, Mapping[str, Any]] | set[str] | list[str],
        incoming_edges: Mapping[str, list[Mapping[str, Any]]],
        outgoing_edges: Mapping[str, list[Mapping[str, Any]]],
        node_roles: Mapping[str, str] | None = None,
        max_depth: int = 4,
        max_paths: int = 8,
    ) -> dict[str, Any]:
        node_set = set(nodes.keys()) if hasattr(nodes, "keys") else set(nodes)
        max_depth = max(1, int(max_depth))
        max_paths = max(1, int(max_paths))

        ranked_upstream = self._walk_and_rank(
            target_tag=target_tag,
            direction="upstream",
            node_set=node_set,
            incoming_edges=incoming_edges,
            outgoing_edges=outgoing_edges,
            node_roles=node_roles or {},
            max_depth=max_depth,
            max_paths=max_paths,
        )

        ranked_downstream = self._walk_and_rank(
            target_tag=target_tag,
            direction="downstream",
            node_set=node_set,
            incoming_edges=incoming_edges,
            outgoing_edges=outgoing_edges,
            node_roles=node_roles or {},
            max_depth=max_depth,
            max_paths=max_paths,
        )

        merged_context = self._merge_parallel_influences(
            target_tag=target_tag,
            ranked_upstream=ranked_upstream,
            ranked_downstream=ranked_downstream,
        )

        return {
            "ranked_upstream": ranked_upstream,
            "ranked_downstream": ranked_downstream,
            "merged_context": merged_context,
        }

    def _walk_and_rank(
        self,
        *,
        target_tag: str,
        direction: str,
        node_set: set[str],
        incoming_edges: Mapping[str, list[Mapping[str, Any]]],
        outgoing_edges: Mapping[str, list[Mapping[str, Any]]],
        node_roles: Mapping[str, str],
        max_depth: int,
        max_paths: int,
    ) -> list[dict[str, Any]]:
        queue: deque[tuple[list[str], list[ChainEdge], set[str], int]] = deque()
        queue.append(([target_tag], [], {target_tag}, 0))

        collected: list[RawPath] = []
        max_expansions = max_paths * 24
        expansions = 0

        while queue and len(collected) < max_paths * 3 and expansions < max_expansions:
            node_path, edge_path, visited, depth = queue.popleft()
            expansions += 1
            current = node_path[-1]

            if depth >= max_depth:
                collected.append(self._rank_path(node_path, edge_path, node_roles, broken=True, break_reason="max_depth"))
                continue

            next_edges = incoming_edges.get(current, []) if direction == "upstream" else outgoing_edges.get(current, [])
            if not next_edges:
                collected.append(self._rank_path(node_path, edge_path, node_roles, broken=False, break_reason="path_end"))
                continue

            progressed = False
            for raw_edge in next_edges:
                edge = self._to_chain_edge(raw_edge)
                neighbor = edge.source if direction == "upstream" else edge.target
                if not neighbor:
                    collected.append(self._rank_path(node_path, edge_path + [edge], node_roles, broken=True, break_reason="empty_neighbor"))
                    continue
                if neighbor in visited:
                    collected.append(self._rank_path(node_path + [neighbor], edge_path + [edge], node_roles, broken=True, break_reason="cycle_detected"))
                    continue
                if neighbor not in node_set:
                    collected.append(self._rank_path(node_path + [neighbor], edge_path + [edge], node_roles, broken=True, break_reason="missing_node"))
                    continue

                progressed = True
                next_nodes = node_path + [neighbor]
                next_visited = set(visited)
                next_visited.add(neighbor)
                queue.append((next_nodes, edge_path + [edge], next_visited, depth + 1))

            if not progressed:
                collected.append(self._rank_path(node_path, edge_path, node_roles, broken=True, break_reason="broken_path"))

        if not collected:
            collected.append(self._rank_path([target_tag], [], node_roles, broken=True, break_reason="no_paths"))

        collected.sort(key=lambda item: item.score, reverse=True)
        return [self._serialize_path(path) for path in collected[:max_paths]]

    def _rank_path(
        self,
        node_path: list[str],
        edge_path: list[ChainEdge],
        node_roles: Mapping[str, str],
        *,
        broken: bool,
        break_reason: str,
    ) -> RawPath:
        if not edge_path:
            weak_links: list[dict[str, Any]] = []
            score = max(0.0, 0.2 - (0.02 * max(0, len(node_path) - 1)))
            return RawPath(nodes=node_path, edges=edge_path, broken=broken, break_reason=break_reason, weak_links=weak_links, score=round(score, 6))

        confidence_values = [max(0.0, min(1.0, edge.confidence)) for edge in edge_path]
        source_weights = [self._source_weight(edge.source_type) for edge in edge_path]
        relation_weights = [self._relation_weight(edge.rel_type) for edge in edge_path]

        role_scores: list[float] = []
        for node in node_path[1:]:
            role = str(node_roles.get(node, "unknown") or "unknown")
            role_scores.append(ROLE_BONUS_WEIGHTS.get(role, self._default_role_bonus))

        confidence_score = sum(confidence_values) / len(confidence_values)
        source_score = sum(source_weights) / len(source_weights)
        relation_score = sum(relation_weights) / len(relation_weights)
        role_bonus = (sum(role_scores) / len(role_scores)) if role_scores else 1.0
        length_penalty = 0.03 * max(0, len(node_path) - 1)

        raw_score = (
            (0.35 * confidence_score)
            + (0.25 * source_score)
            + (0.25 * relation_score)
            + (0.15 * role_bonus)
            - length_penalty
        )

        weak_links: list[dict[str, Any]] = []
        for index, edge in enumerate(edge_path):
            reasons: list[str] = []
            if edge.confidence < 0.8:
                reasons.append("low_confidence")
            if self._source_weight(edge.source_type) < 0.8:
                reasons.append("weak_source_type")
            if self._relation_weight(edge.rel_type) < 0.8:
                reasons.append("weak_relation_type")
            if reasons:
                weak_links.append(
                    {
                        "index": index,
                        "source": edge.source,
                        "target": edge.target,
                        "rel_type": edge.rel_type,
                        "confidence": edge.confidence,
                        "reasons": reasons,
                    }
                )

        return RawPath(
            nodes=node_path,
            edges=edge_path,
            broken=broken,
            break_reason=break_reason,
            weak_links=weak_links,
            score=round(max(0.0, raw_score), 6),
        )

    def _serialize_path(self, path: RawPath) -> dict[str, Any]:
        return {
            "nodes": list(path.nodes),
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "rel_type": edge.rel_type,
                    "confidence": edge.confidence,
                    "source_type": edge.source_type,
                }
                for edge in path.edges
            ],
            "score": path.score,
            "broken": path.broken,
            "break_reason": path.break_reason,
            "weak_links": path.weak_links,
        }

    def _merge_parallel_influences(
        self,
        *,
        target_tag: str,
        ranked_upstream: list[dict[str, Any]],
        ranked_downstream: list[dict[str, Any]],
    ) -> dict[str, Any]:
        upstream_tags: set[str] = set()
        downstream_tags: set[str] = set()

        for chain in ranked_upstream:
            for node in chain.get("nodes", []):
                if node and node != target_tag:
                    upstream_tags.add(node)

        for chain in ranked_downstream:
            for node in chain.get("nodes", []):
                if node and node != target_tag:
                    downstream_tags.add(node)

        return {
            "parallel_upstream_tags": sorted(upstream_tags),
            "parallel_downstream_tags": sorted(downstream_tags),
            "parallel_context_tags": sorted(upstream_tags | downstream_tags),
        }

    def _to_chain_edge(self, raw_edge: Mapping[str, Any]) -> ChainEdge:
        source = str(raw_edge.get("source", "") or "").strip()
        target = str(raw_edge.get("target", "") or "").strip()
        rel_type = str(raw_edge.get("edge_type") or raw_edge.get("rel_type") or raw_edge.get("type") or "RELATED_TO").strip() or "RELATED_TO"
        source_type = str(raw_edge.get("source_type") or "explicit").strip().lower() or "explicit"
        confidence_raw = raw_edge.get("confidence")
        confidence = float(confidence_raw) if confidence_raw is not None else 1.0
        confidence = max(0.0, min(1.0, confidence))
        return ChainEdge(source=source, target=target, rel_type=rel_type, confidence=confidence, source_type=source_type)

    def _source_weight(self, source_type: str) -> float:
        normalized = str(source_type or "").strip().lower()
        if normalized.startswith("row:"):
            normalized = normalized.split(":", 1)[1]
        return SOURCE_TYPE_WEIGHTS.get(normalized, self._default_source_weight)

    def _relation_weight(self, rel_type: str) -> float:
        normalized = str(rel_type or "RELATED_TO").strip().upper() or "RELATED_TO"
        return RELATION_TYPE_WEIGHTS.get(normalized, self._default_relation_weight)
