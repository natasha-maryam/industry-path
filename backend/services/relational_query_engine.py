from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from services.graph_service import graph_service
from services.uns_core import uns_core


class RelationalQueryEngine:
    def _canonical_edges(self, project_id: str | None) -> list[dict[str, Any]]:
        if project_id:
            graph = graph_service.get_graph(project_id)
            return [edge.model_dump() if hasattr(edge, "model_dump") else dict(edge) for edge in graph.edges]
        return uns_core.get_edges()

    @staticmethod
    def _adjacency(edges: list[dict[str, Any]]) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[tuple[str, str], str]]:
        outbound: dict[str, set[str]] = defaultdict(set)
        inbound: dict[str, set[str]] = defaultdict(set)
        edge_types: dict[tuple[str, str], str] = {}

        for edge in edges:
            source = str(edge.get("source") or "").strip()
            target = str(edge.get("target") or "").strip()
            edge_type = str(edge.get("edge_type") or "RELATED_TO").strip() or "RELATED_TO"
            if not source or not target or source == target:
                continue
            outbound[source].add(target)
            inbound[target].add(source)
            edge_types[(source, target)] = edge_type

        return outbound, inbound, edge_types

    def trace(self, tag: str, project_id: str | None = None, max_depth: int = 6) -> dict[str, Any]:
        start_tag = str(tag or "").strip()
        if not start_tag:
            raise ValueError("tag is required")

        edges = self._canonical_edges(project_id)
        outbound, inbound, edge_types = self._adjacency(edges)

        steps: list[dict[str, Any]] = []
        steps.append({"tag": start_tag, "depth": 0, "direction": "self", "edge_type": None})

        def traverse(direction: str) -> None:
            adjacency = inbound if direction == "upstream" else outbound
            queue: deque[tuple[str, int]] = deque([(start_tag, 0)])
            visited: set[str] = {start_tag}

            while queue:
                current, depth = queue.popleft()
                if depth >= max_depth:
                    continue

                for nxt in sorted(adjacency.get(current, set())):
                    if nxt in visited:
                        continue
                    visited.add(nxt)
                    queue.append((nxt, depth + 1))
                    steps.append(
                        {
                            "tag": nxt,
                            "depth": depth + 1,
                            "direction": direction,
                            "edge_type": edge_types.get((nxt, current)) if direction == "upstream" else edge_types.get((current, nxt)),
                        }
                    )

        traverse("upstream")
        traverse("downstream")

        steps.sort(key=lambda item: (item["depth"], item["direction"], item["tag"]))
        return {
            "tag": start_tag,
            "project_id": project_id,
            "path": [item["tag"] for item in steps],
            "steps": steps,
        }

    def find_loops(self, project_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        edges = self._canonical_edges(project_id)
        outbound, _, _ = self._adjacency(edges)

        loops: list[list[str]] = []

        def dfs(start: str, node: str, path: list[str], seen: set[str]) -> None:
            if len(loops) >= limit:
                return
            for nxt in sorted(outbound.get(node, set())):
                if nxt == start and len(path) >= 2:
                    loops.append([*path, start])
                    continue
                if nxt in seen or len(path) >= 8:
                    continue
                dfs(start, nxt, [*path, nxt], {*(seen), nxt})

        for tag in sorted(outbound.keys()):
            dfs(tag, tag, [tag], {tag})
            if len(loops) >= limit:
                break

        return {
            "project_id": project_id,
            "loops": loops,
            "count": len(loops),
            "note": "Analytical loops from canonical graph edges; does not replace control loop module semantics.",
        }

    def bottlenecks(self, project_id: str | None = None, limit: int = 10) -> dict[str, Any]:
        edges = self._canonical_edges(project_id)
        outbound, inbound, _ = self._adjacency(edges)

        candidates: list[dict[str, Any]] = []
        all_nodes = sorted(set(outbound.keys()) | set(inbound.keys()))
        for node in all_nodes:
            in_degree = len(inbound.get(node, set()))
            out_degree = len(outbound.get(node, set()))
            score = in_degree * out_degree
            if score <= 0:
                continue
            candidates.append(
                {
                    "tag": node,
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "score": score,
                }
            )

        candidates.sort(key=lambda item: (-item["score"], -item["in_degree"], item["tag"]))
        top = candidates[: max(1, int(limit))]

        return {
            "project_id": project_id,
            "bottlenecks": top,
            "count": len(top),
        }


relational_query_engine = RelationalQueryEngine()
