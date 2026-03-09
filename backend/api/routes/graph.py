from fastapi import APIRouter

from models.graph import PlantGraph, TraceResponse
from services.graph_service import graph_service

router = APIRouter(prefix="/projects/{project_id}", tags=["graph"])


@router.get("/graph", response_model=PlantGraph)
def get_plant_graph(project_id: str) -> PlantGraph:
    return graph_service.get_graph(project_id)


@router.get("/trace/{node_id}", response_model=TraceResponse)
def trace_signal(project_id: str, node_id: str) -> TraceResponse:
    return graph_service.trace(project_id, node_id)


@router.get("/nodes/{node_id}")
def node_details(project_id: str, node_id: str) -> dict[str, object]:
    return graph_service.node_details(project_id, node_id)
