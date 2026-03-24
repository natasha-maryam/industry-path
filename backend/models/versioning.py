from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VersionCommitRequest(BaseModel):
    project_id: str
    trigger_source: str
    summary: str | None = None


class VersionSnapshotRequest(BaseModel):
    project_id: str
    trigger_source: str
    summary: str | None = None


class VersionRollbackRequest(BaseModel):
    project_id: str
    version_tag: str


class VersionDiffQuery(BaseModel):
    compare_to: str | None = None


class VersionActionResponse(BaseModel):
    status: str
    project_id: str
    version_tag: str
    commit_hash: str | None = None
    snapshot_path: str | None = None
    trigger_source: str | None = None
    summary: str | None = None
    artifact_status: dict[str, str] = Field(default_factory=dict)
    metadata_id: str | None = None
    dolt: dict[str, Any] = Field(default_factory=dict)


class VersionHistoryResponse(BaseModel):
    project_id: str
    records: list[dict[str, Any]] = Field(default_factory=list)


class VersionDiffResponse(BaseModel):
    project_id: str
    version_a: str
    version_b: str
    logic_diff: dict[str, str] = Field(default_factory=dict)
    metadata_diff: dict[str, Any] = Field(default_factory=dict)
