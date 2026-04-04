from __future__ import annotations

from fastapi import APIRouter, Header, Response, status
from typing import Optional

from models.project import ActiveProjectUpdate, Project, ProjectCreate, ProjectUpdate
from services.project_service import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> list[Project]:
    return project_service.list_projects(actor_email=x_user_email)


@router.post("", response_model=Project)
def create_project(payload: ProjectCreate, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> Project:
    return project_service.create_project(payload, actor_email=x_user_email)


@router.get("/active/current", response_model=Optional[Project])
def get_active_project(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> Optional[Project]:
    return project_service.get_active_project(actor_email=x_user_email)


@router.put("/active", response_model=Project)
def update_active_project(payload: ActiveProjectUpdate, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> Project:
    return project_service.set_active_project(payload.project_id, actor_email=x_user_email)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> Project:
    return project_service.get_project(project_id, actor_email=x_user_email)


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, payload: ProjectUpdate, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> Project:
    return project_service.update_project(project_id, payload, actor_email=x_user_email)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> Response:
    project_service.delete_project(project_id, actor_email=x_user_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
