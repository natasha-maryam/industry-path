from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PLCUploadDocumentType = Literal[
    "plc_project_file",
    "logic_export",
    "tag_list",
    "io_table",
    "pid_pdf",
    "control_narrative",
    "unknown_document",
]

PLCSourceFormat = Literal[
    "rockwell_l5x",
    "rockwell_acd",
    "siemens_xml",
    "siemens_ap16",
    "codesys_project",
    "codesys_xml",
    "beckhoff_tsproj",
    "openplc_st",
    "iec_st",
    "ladder_xml",
    "csv_io_table",
    "loose_st_files",
    "unknown",
]

ExtractionStatus = Literal["ok", "partial", "unsupported", "error"]


class ExtractedTag(BaseModel):
    raw_tag: str
    canonical_tag: str
    signal_type: str | None = None
    device_type: str | None = None
    source_hint: str | None = None


class ExtractedVariable(BaseModel):
    name: str
    data_type: str | None = None
    scope: str | None = None


class ExtractedRoutine(BaseModel):
    name: str
    routine_type: str | None = None
    language: str | None = None


class ExtractedDevice(BaseModel):
    name: str
    device_type: str | None = None
    address: str | None = None


class ExtractedIOEntry(BaseModel):
    tag: str | None = None
    address: str | None = None
    io_type: str | None = None
    description: str | None = None


class ExtractedLogicReference(BaseModel):
    source: str
    target: str
    reference_type: str


class ReverseEngineeringFileResult(BaseModel):
    original_name: str
    stored_name: str
    document_type: PLCUploadDocumentType
    detected_format: PLCSourceFormat
    status: ExtractionStatus
    tags: list[ExtractedTag] = Field(default_factory=list)
    variables: list[ExtractedVariable] = Field(default_factory=list)
    routines: list[ExtractedRoutine] = Field(default_factory=list)
    devices: list[ExtractedDevice] = Field(default_factory=list)
    io_entries: list[ExtractedIOEntry] = Field(default_factory=list)
    logic_references: list[ExtractedLogicReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    extracted_output_path: str | None = None


class PLCPhase1ExtractionResponse(BaseModel):
    project_id: str
    run_id: str
    generated_at: datetime
    status: ExtractionStatus
    extracted_root: str
    files: list[ReverseEngineeringFileResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    next_phase_ready_for: list[str] = Field(
        default_factory=lambda: [
            "io_mapping_reconstruction",
            "control_loop_detection",
            "plant_graph_reconstruction",
            "logic_normalization",
        ]
    )
