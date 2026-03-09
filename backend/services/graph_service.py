import json
from collections import defaultdict, deque

from db.neo4j import neo4j_client
from models.graph import GraphEdge, GraphNode, PlantGraph, TraceResponse
from services.project_service import project_service


class GraphService:
    def _graph_file(self, project_id: str):
        paths = project_service.workspace_paths(project_id)
        return paths.plant_graph / "latest_graph.json"

    def store_graph(self, project_id: str, nodes: list[dict], edges: list[dict]) -> PlantGraph:
        project_service.ensure_project(project_id)

        node_models = [GraphNode.model_validate(node) for node in nodes]
        edge_models = [GraphEdge.model_validate(edge) for edge in edges]

        graph_file = self._graph_file(project_id)
        payload = {
            "project_id": project_id,
            "nodes": [node.model_dump() for node in node_models],
            "edges": [edge.model_dump() for edge in edge_models],
        }
        graph_file.write_text(json.dumps(payload, indent=2))

        try:
            neo4j_client.clear_project_graph(project_id)
            neo4j_client.write_project_graph(
                project_id,
                nodes=[node.model_dump() for node in node_models],
                edges=[edge.model_dump() for edge in edge_models],
            )
        except Exception:
            # Fallback cache remains available when Neo4j is offline.
            pass

        return PlantGraph(project_id=project_id, nodes=node_models, edges=edge_models)

    def _load_graph(self, project_id: str) -> PlantGraph:
        try:
            nodes, edges = neo4j_client.fetch_project_graph(project_id)
            if nodes or edges:
                node_models = [GraphNode.model_validate(node) for node in nodes]
                edge_models = [GraphEdge.model_validate(edge) for edge in edges]
                return PlantGraph(project_id=project_id, nodes=node_models, edges=edge_models)
        except Exception:
            pass

        graph_file = self._graph_file(project_id)
        if not graph_file.exists():
            return PlantGraph(project_id=project_id, nodes=[], edges=[])

        payload = json.loads(graph_file.read_text())
        nodes = [GraphNode.model_validate(node) for node in payload.get("nodes", [])]
        edges = [GraphEdge.model_validate(edge) for edge in payload.get("edges", [])]
        return PlantGraph(project_id=project_id, nodes=nodes, edges=edges)

    def get_graph(self, project_id: str) -> PlantGraph:
        project_service.ensure_project(project_id)
        return self._load_graph(project_id)

    def node_details(self, project_id: str, node_id: str) -> dict[str, object]:
        graph = self._load_graph(project_id)
        node = next((item for item in graph.nodes if item.id == node_id), None)
        if node is None:
            return {"project_id": project_id, "node_id": node_id, "found": False}

        inbound = [edge.source for edge in graph.edges if edge.target == node_id]
        outbound = [edge.target for edge in graph.edges if edge.source == node_id]
        return {
            "project_id": project_id,
            "node_id": node_id,
            "found": True,
            "node": node.model_dump(),
            "inbound": inbound,
            "outbound": outbound,
        }

    def trace(self, project_id: str, node_id: str) -> TraceResponse:
        project_service.ensure_project(project_id)
        graph = self._load_graph(project_id)
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge.target)

        if node_id not in {node.id for node in graph.nodes}:
            return TraceResponse(project_id=project_id, node_id=node_id, path=[])

        queue: deque[list[str]] = deque([[node_id]])
        visited: set[str] = {node_id}
        longest_path: list[str] = [node_id]

        while queue:
            current_path = queue.popleft()
            tail = current_path[-1]
            if len(current_path) > len(longest_path):
                longest_path = current_path

            for neighbor in adjacency.get(tail, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(current_path + [neighbor])

        return TraceResponse(project_id=project_id, node_id=node_id, path=longest_path)


graph_service = GraphService()
