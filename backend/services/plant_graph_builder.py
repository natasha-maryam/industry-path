from __future__ import annotations

from dataclasses import dataclass

from db.neo4j import neo4j_client
from models.graph import PlantGraph
from services.graph_build_service import graph_build_service
from services.graph_service import graph_service


@dataclass
class GraphRepository:
    """Repository abstraction with in-memory/filesystem fallback and optional Neo4j adapter."""

    def load(self, project_id: str) -> PlantGraph:
        try:
            nodes, edges = neo4j_client.fetch_project_graph(project_id)
            if nodes or edges:
                return PlantGraph(project_id=project_id, nodes=nodes, edges=edges)
        except Exception:
            pass
        return graph_service.get_graph(project_id)

    def save(self, project_id: str, nodes: list[dict], edges: list[dict]) -> None:
        graph_service.store_graph(project_id, nodes, edges)


class PlantGraphBuilder:
    def __init__(self) -> None:
        self.repo = GraphRepository()

    def build_and_store(self, project_id: str, entities: list, relationships: list) -> PlantGraph:
        nodes, edges = graph_build_service.build(entities, relationships)
        self.repo.save(project_id, nodes, edges)
        return graph_service.get_graph(project_id)


plant_graph_builder = PlantGraphBuilder()
