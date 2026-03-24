from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RuntimeQueueRequest(BaseModel):
    project_id: str
    updates: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ScriptQueueRequest(BaseModel):
    script: str
    project_id: str | None = None


class ConnectorHealthItem(BaseModel):
    connector_type: str
    configured: bool
    healthy: bool
    message: str
    updated_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConnectorHealthResponse(BaseModel):
    connectors: list[ConnectorHealthItem] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event_type: str
    actor: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class HealthResponse(BaseModel):
    status: str
    services: dict[str, Any] = Field(default_factory=dict)
    timestamp: str
