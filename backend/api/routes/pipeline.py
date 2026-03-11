from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from models.graph import PlantGraph
from models.logic import LogicGenerateRequest, LogicGenerationResult
from services.deploy_service import deploy_service
from services.graph_service import graph_service
from services.logic_service import logic_service
from services.parse_service import parse_service
from services.project_service import project_service
from services.upload_service import upload_service

router = APIRouter(tags=["pipeline"])


class ProjectScopedRequest(BaseModel):
    project_id: str


class ParseScopedRequest(BaseModel):
    project_id: str
    file_ids: list[str] = Field(default_factory=list)


class DeployScopedRequest(BaseModel):
    project_id: str
    runtime: str = "OpenPLC"


@router.post("/upload")
async def upload_alias(
    project_id: str = Form(...),
    files: list[UploadFile] = File(...),
    document_types: list[str] | None = Form(default=None),
):
    return await upload_service.save_files(project_id, files, document_types)


@router.post("/parse")
def parse_alias(payload: ParseScopedRequest):
    return parse_service.parse_project(payload.project_id, file_ids=payload.file_ids)


@router.post("/generate-logic", response_model=LogicGenerationResult)
def generate_logic_alias(payload: ProjectScopedRequest):
    return logic_service.generate(payload.project_id, strategy="deterministic")


@router.post("/validate-logic")
def validate_logic_alias(payload: ProjectScopedRequest):
    return logic_service.validate_latest_st(payload.project_id)


@router.post("/run-simulation")
def run_simulation_alias(payload: ProjectScopedRequest):
    return logic_service.run_virtual_commissioning(payload.project_id)


@router.post("/deploy-plc")
def deploy_plc_alias(payload: DeployScopedRequest):
    return deploy_service.deploy(project_id=payload.project_id, runtime=payload.runtime)


@router.get("/plant-graph", response_model=PlantGraph)
def plant_graph_alias(project_id: str):
    return graph_service.get_graph(project_id)


@router.get("/logic-files")
def logic_files_alias(project_id: str):
    root = project_service.workspace_paths(project_id).control_logic
    if not root.exists():
        raise HTTPException(status_code=404, detail="No generated control_logic directory found for project")
    files = sorted(str(path.relative_to(root)) for path in root.rglob("*.st"))
    return {"project_id": project_id, "output_root": str(root), "files": files}
