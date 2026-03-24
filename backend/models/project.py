from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


ProjectStatus = Literal["draft", "active", "archived"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industry: str = Field(default="general", min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    plc_runtime: str = Field(default="beremiz", min_length=2, max_length=120)
    owner: str | None = Field(default="system", max_length=120)
    active_version: int = Field(default=1, ge=1)
    status: ProjectStatus = "draft"


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    industry: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    plc_runtime: str | None = Field(default=None, min_length=2, max_length=120)
    owner: str | None = Field(default=None, max_length=120)
    active_version: int | None = Field(default=None, ge=1)
    status: ProjectStatus | None = None


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    industry: str = "general"
    description: str | None = None
    plc_runtime: str = "beremiz"
    owner: str = "system"
    status: ProjectStatus = "draft"
    active_version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectContext(BaseModel):
    project_id: str


class ActiveProjectUpdate(BaseModel):
    project_id: str
