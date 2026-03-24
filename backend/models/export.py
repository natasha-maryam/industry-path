from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ExportVendor = Literal["siemens", "rockwell", "codesys", "beckhoff", "openplc"]


class ExportRequest(BaseModel):
    project_id: str
    vendor: ExportVendor


class ExportResponse(BaseModel):
    export_id: str
    project_id: str
    project_name: str
    vendor: ExportVendor
    generated_at: datetime
    files: list[str] = Field(default_factory=list)
    download_url: str
    package_path: str | None = None
    artifact_name: str | None = None
    logic_block_count: int = 0
    tag_count: int = 0
