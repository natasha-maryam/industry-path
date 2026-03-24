from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from ..common import LogicModel, VendorExportResult
from ..vendor_base import BaseVendorExporter


class SiemensExporter(BaseVendorExporter):
    vendor_key = "siemens"

    @staticmethod
    def _sanitize(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned or "Block"

    def _block_file_name(self, block_name: str, seen: set[str]) -> str:
        lower = block_name.lower()
        if match := re.search(r"pump[-_ ]?(\d+)", lower):
            stem = f"Pump_{match.group(1)}"
        elif match := re.search(r"valve[-_ ]?(\d+)", lower):
            stem = f"Valve_{match.group(1)}"
        elif match := re.search(r"loop[-_ ]?(\d+)", lower):
            stem = f"Loop_{match.group(1)}"
        elif "main" in lower:
            stem = f"Main_{self._sanitize(block_name)}"
        else:
            stem = self._sanitize(block_name)

        name = stem
        idx = 2
        while f"{name}.scl" in seen:
            name = f"{stem}_{idx}"
            idx += 1
        seen.add(f"{name}.scl")
        return f"{name}.scl"

    @staticmethod
    def _build_tags_xml(project_id: str, tags: list[dict[str, str]]) -> str:
        root = ET.Element("PlantTags", attrib={"projectId": project_id})
        for tag in tags:
            ET.SubElement(
                root,
                "Tag",
                attrib={
                    "name": tag["name"],
                    "type": tag["type"],
                    "metadata": tag.get("metadata", ""),
                },
            )
        body = ET.tostring(root, encoding="unicode")
        return f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n{body}\n"

    def export(self, output_root: Path, logic_model: LogicModel) -> VendorExportResult:
        # Spec-defined output: TIA_Project/ProgramBlocks + TIA_Project/Tags
        tia_root = output_root / "TIA_Project"
        program_blocks_root = tia_root / "ProgramBlocks"
        tags_root = tia_root / "Tags"
        program_blocks_root.mkdir(parents=True, exist_ok=True)
        tags_root.mkdir(parents=True, exist_ok=True)

        all_blocks = [
            *logic_model.equipment_routines,
            *logic_model.loops,
            *logic_model.programs,
            *logic_model.function_blocks,
            *logic_model.interlocks,
            *logic_model.alarms,
        ]
        if not all_blocks and logic_model.source_files:
            from ..common import LogicBlock

            all_blocks = [
                LogicBlock(
                    name="MainProgram",
                    kind="PROGRAM",
                    content=logic_model.source_files[0].content,
                    source_file=logic_model.source_files[0].path,
                )
            ]

        seen_files: set[str] = set()
        generated_files: list[str] = []
        for block in all_blocks:
            file_name = self._block_file_name(block.name, seen_files)
            target = program_blocks_root / file_name
            target.write_text(block.content, encoding="utf-8")
            generated_files.append(str(target.relative_to(output_root)))

        tags = [{"name": t.name, "type": t.data_type, "metadata": t.metadata} for t in logic_model.tags]
        tags_file = tags_root / "plant_tags.xml"
        tags_file.write_text(self._build_tags_xml(logic_model.project_id, tags), encoding="utf-8")
        generated_files.append(str(tags_file.relative_to(output_root)))

        zip_path = output_root / "TIA_Project.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(tia_root.rglob("*")):
                if file.is_file():
                    archive.write(file, arcname=str(file.relative_to(output_root)))

        return VendorExportResult(
            artifact_name="TIA_Project.zip",
            artifact_path=zip_path,
            generated_files=sorted(generated_files),
            logic_block_count=len(all_blocks),
            tag_count=len(tags),
            notes=["TIA proprietary internals intentionally not implemented in phase scaffold."],
        )
