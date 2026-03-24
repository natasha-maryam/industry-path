from __future__ import annotations

import re
from collections import OrderedDict

from .common import LogicBlock, LogicModel, LogicTag, STSourceFile


_START_PATTERN = re.compile(r"^\s*(PROGRAM|FUNCTION_BLOCK|FUNCTION)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_END_TOKEN = {
    "PROGRAM": "END_PROGRAM",
    "FUNCTION_BLOCK": "END_FUNCTION_BLOCK",
    "FUNCTION": "END_FUNCTION",
}
_VAR_DECL_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^;]+);", re.MULTILINE)
_TAG_PATTERN = re.compile(r"\b([A-Za-z]{1,6}[-_ ]?\d{1,5}[A-Za-z0-9]{0,4})\b")


def _parse_blocks(st_files: list[STSourceFile]) -> list[LogicBlock]:
    blocks: list[LogicBlock] = []
    for source in st_files:
        lines = source.content.splitlines()
        active_kind = ""
        active_name = ""
        collected: list[str] = []

        for line in lines:
            if not active_kind:
                if match := _START_PATTERN.match(line):
                    active_kind = match.group(1).upper()
                    active_name = match.group(2)
                    collected = [line]
                continue

            collected.append(line)
            if line.strip().upper().startswith(_END_TOKEN.get(active_kind, "END")):
                blocks.append(
                    LogicBlock(
                        name=active_name,
                        kind=active_kind,
                        content="\n".join(collected).strip() + "\n",
                        source_file=source.path,
                    )
                )
                active_kind = ""
                active_name = ""
                collected = []

        if active_kind and collected:
            blocks.append(
                LogicBlock(
                    name=active_name,
                    kind=active_kind,
                    content="\n".join(collected).strip() + "\n",
                    source_file=source.path,
                )
            )

    if not blocks and st_files:
        blocks.append(
            LogicBlock(
                name="MainProgram",
                kind="PROGRAM",
                content=st_files[0].content,
                source_file=st_files[0].path,
            )
        )
    return blocks


def _categorize_block(block: LogicBlock) -> tuple[bool, bool, bool, bool, bool]:
    lower = block.name.lower()
    is_loop = "loop" in lower or "pid" in lower
    is_interlock = "interlock" in lower or "perm" in lower
    is_alarm = "alarm" in lower or "trip" in lower
    is_equipment = any(token in lower for token in ("pump", "valve", "tank", "blower", "motor", "compressor"))
    is_main = "main" in lower
    return is_loop, is_interlock, is_alarm, is_equipment, is_main


def _collect_tags(st_files: list[STSourceFile]) -> list[LogicTag]:
    tags: OrderedDict[str, LogicTag] = OrderedDict()
    for source in st_files:
        for name, dtype in _VAR_DECL_PATTERN.findall(source.content):
            tags.setdefault(name, LogicTag(name=name, data_type=dtype.strip(), metadata="variable_declaration"))

        for candidate in _TAG_PATTERN.findall(source.content):
            normalized = candidate.replace(" ", "_").replace("-", "_")
            tags.setdefault(normalized, LogicTag(name=normalized, data_type="UNKNOWN", metadata="tag_pattern"))
    return list(tags.values())


def build_logic_model(project_id: str, project_name: str, owner: str, st_files: list[STSourceFile]) -> LogicModel:
    blocks = _parse_blocks(st_files)

    programs: list[LogicBlock] = []
    function_blocks: list[LogicBlock] = []
    equipment_routines: list[LogicBlock] = []
    loops: list[LogicBlock] = []
    interlocks: list[LogicBlock] = []
    alarms: list[LogicBlock] = []

    for block in blocks:
        if block.kind == "PROGRAM":
            programs.append(block)
        if block.kind == "FUNCTION_BLOCK":
            function_blocks.append(block)

        is_loop, is_interlock, is_alarm, is_equipment, _ = _categorize_block(block)
        if is_loop:
            loops.append(block)
        if is_interlock:
            interlocks.append(block)
        if is_alarm:
            alarms.append(block)
        if is_equipment:
            equipment_routines.append(block)

    io_metadata = [
        {"name": tag.name, "type": tag.data_type}
        for tag in _collect_tags(st_files)
        if any(token in tag.name.upper() for token in ("AI", "AO", "DI", "DO", "I_", "Q_"))
    ]

    return LogicModel(
        project_id=project_id,
        project_name=project_name,
        owner=owner,
        source_files=st_files,
        programs=programs,
        function_blocks=function_blocks,
        equipment_routines=equipment_routines,
        loops=loops,
        interlocks=interlocks,
        alarms=alarms,
        tags=_collect_tags(st_files),
        io_metadata=io_metadata,
    )
