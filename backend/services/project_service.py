from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import UUID, uuid4

from fastapi import HTTPException

from db.postgres import postgres_client
from models.file import WorkspacePaths
from models.project import Project, ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, workspace_root: Path | None = None) -> None:
        default_root = Path(__file__).resolve().parents[2] / "storage" / "projects"
        self.workspace_root = workspace_root or default_root
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[Project]:
        rows = postgres_client.fetch_all(
            """
            SELECT id, name, industry, description, plc_runtime, owner, status, active_version, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC
            """
        )
        return [Project.model_validate(row) for row in rows]

    def create_project(self, payload: ProjectCreate) -> Project:
        now = datetime.now(timezone.utc)
        project = Project(
            id=uuid4(),
            name=payload.name,
            industry=payload.industry,
            description=payload.description,
            plc_runtime=payload.plc_runtime,
            owner=payload.owner or "system",
            status=payload.status,
            active_version=payload.active_version,
            created_at=now,
            updated_at=now,
        )
        postgres_client.execute(
            """
            INSERT INTO projects (id, name, industry, description, plc_runtime, owner, status, active_version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(project.id),
                project.name,
                project.industry,
                project.description,
                project.plc_runtime,
                project.owner,
                project.status,
                project.active_version,
                project.created_at,
                project.updated_at,
            ),
        )
        self._ensure_workspace(str(project.id))
        return project

    def get_project(self, project_id: str) -> Project:
        row = postgres_client.fetch_one(
            """
            SELECT id, name, industry, description, plc_runtime, owner, status, active_version, created_at, updated_at
            FROM projects
            WHERE id = %s
            """,
            (project_id,),
        )
        if row is None:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
        return Project.model_validate(row)

    def update_project(self, project_id: str, payload: ProjectUpdate) -> Project:
        current = self.get_project(project_id)
        update_data = payload.model_dump(exclude_none=True)
        if not update_data:
            return current

        updated = current.model_copy(update=update_data)
        updated.updated_at = datetime.now(timezone.utc)

        postgres_client.execute(
            """
            UPDATE projects
            SET name = %s,
                industry = %s,
                description = %s,
                plc_runtime = %s,
                owner = %s,
                status = %s,
                active_version = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (
                updated.name,
                updated.industry,
                updated.description,
                updated.plc_runtime,
                updated.owner,
                updated.status,
                updated.active_version,
                updated.updated_at,
                project_id,
            ),
        )

        from services.versioning_trigger_service import versioning_trigger_service

        versioning_trigger_service.trigger_auto_commit(
            project_id=project_id,
            trigger_source="Configuration Changed",
            summary="Project configuration metadata updated.",
        )

        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> None:
        self.get_project(project_id)
        postgres_client.execute("DELETE FROM projects WHERE id = %s", (project_id,))

    def ensure_project(self, project_id: str) -> Project:
        return self.get_project(project_id)

    def get_active_project(self) -> Project | None:
        row = postgres_client.fetch_one(
            """
            SELECT id, name, industry, description, plc_runtime, owner, status, active_version, created_at, updated_at
            FROM projects
            WHERE status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        )
        return Project.model_validate(row) if row else None

    def set_active_project(self, project_id: str) -> Project:
        active = self.get_project(project_id)
        if active.status == "archived":
            raise HTTPException(status_code=400, detail="Archived project cannot be set active")

        now = datetime.now(timezone.utc)
        postgres_client.execute(
            """
            UPDATE projects
            SET status = 'draft',
                updated_at = %s
            WHERE id <> %s
              AND status = 'active'
            """,
            (now, project_id),
        )
        postgres_client.execute(
            """
            UPDATE projects
            SET status = 'active',
                updated_at = %s
            WHERE id = %s
            """,
            (now, project_id),
        )
        return self.get_project(project_id)

    def workspace_paths(self, project_id: str) -> WorkspacePaths:
        self.ensure_project(project_id)
        root = self.workspace_root / project_id
        self._ensure_workspace(project_id)

        return WorkspacePaths(
            root=root,
            documents=root / "documents",
            uploads=root / "documents",
            plant_graph=root / "plant_graph",
            control_logic=root / "control_logic",
            simulation_models=root / "simulation_models",
            io_mapping=root / "io_mapping",
            runtime=root / "runtime",
            monitoring=root / "monitoring",
            snapshots=root / "snapshots",
        )

    def _ensure_workspace(self, project_id: str) -> None:
        root = self.workspace_root / project_id
        subdirs: Iterable[Path] = (
            root / "documents",
            root / "uploads",
            root / "plant_graph",
            root / "control_logic",
            root / "simulation_models",
            root / "io_mapping",
            root / "runtime",
            root / "monitoring",
            root / "snapshots",
        )
        for directory in subdirs:
            directory.mkdir(parents=True, exist_ok=True)

project_service = ProjectService()
