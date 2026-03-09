from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProjectFile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    original_name: str
    stored_name: str
    file_type: str = "application/octet-stream"
    document_type: str = "unknown_document"
    file_path: str
    file_size: int | None = None
    upload_status: str = "uploaded"
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UploadResult(BaseModel):
    project_id: str
    files: list[ProjectFile]


class WorkspacePaths(BaseModel):
    root: Path
    uploads: Path
    plant_graph: Path
    control_logic: Path
    simulation_models: Path
    io_mapping: Path
    runtime: Path
    monitoring: Path
    snapshots: Path
