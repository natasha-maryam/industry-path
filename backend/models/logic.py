from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LogicGenerateRequest(BaseModel):
    strategy: str = Field(default="default")


class LogicArtifact(BaseModel):
    project_id: str
    file_name: str = "main.st"
    code: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeployResult(BaseModel):
    project_id: str
    runtime: str
    status: str
    details: str
