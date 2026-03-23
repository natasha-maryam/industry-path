from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


ExportVendor = Literal["siemens", "rockwell", "codesys", "beckhoff", "openplc"]


@dataclass(frozen=True)
class STSourceFile:
    path: str
    content: str
    lines: int


@dataclass(frozen=True)
class LogicBlock:
    name: str
    kind: str
    content: str
    source_file: str


@dataclass(frozen=True)
class LogicTag:
    name: str
    data_type: str
    metadata: str = ""


@dataclass(frozen=True)
class LogicModel:
    project_id: str
    project_name: str
    owner: str
    source_files: list[STSourceFile]
    programs: list[LogicBlock] = field(default_factory=list)
    function_blocks: list[LogicBlock] = field(default_factory=list)
    equipment_routines: list[LogicBlock] = field(default_factory=list)
    loops: list[LogicBlock] = field(default_factory=list)
    interlocks: list[LogicBlock] = field(default_factory=list)
    alarms: list[LogicBlock] = field(default_factory=list)
    tags: list[LogicTag] = field(default_factory=list)
    io_metadata: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class VendorExportResult:
    artifact_name: str
    artifact_path: Path
    generated_files: list[str]
    logic_block_count: int
    tag_count: int
    notes: list[str] = field(default_factory=list)
