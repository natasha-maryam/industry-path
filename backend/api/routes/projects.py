from __future__ import annotations

from fastapi import APIRouter, Response, status
from typing import Optional

from models.project import ActiveProjectUpdate, Project, ProjectCreate, ProjectUpdate
from services.project_service import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects() -> list[Project]:
    return project_service.list_projects()


@router.post("", response_model=Project)
def create_project(payload: ProjectCreate) -> Project:
    return project_service.create_project(payload)


@router.get("/active/current", response_model=Optional[Project])
def get_active_project() -> Optional[Project]:
    return project_service.get_active_project()


@router.put("/active", response_model=Project)
def update_active_project(payload: ActiveProjectUpdate) -> Project:
    return project_service.set_active_project(payload.project_id)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    return project_service.get_project(project_id)


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, payload: ProjectUpdate) -> Project:
    return project_service.update_project(project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str) -> Response:
    project_service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
