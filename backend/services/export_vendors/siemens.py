from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from jinja2 import Environment

from services.export_vendors.base import BaseVendorRenderer


class SiemensRenderer(BaseVendorRenderer):
    vendor_key = "siemens"
    vendor_display_name = "Siemens TIA Portal"
    template_name = "siemens_tia_project.j2"

    def output_filename(self, project_name: str) -> str:
        normalized = "_".join(part for part in project_name.strip().split() if part) or "project"
        return f"{normalized}.scl"

    @staticmethod
    def _sanitize_name(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned or "Block"

    def _unit_file_name(self, unit_name: str, seen: set[str]) -> str:
        lower = unit_name.lower()
        if match := re.search(r"pump[-_ ]?(\d+)", lower):
            stem = f"Pump_{match.group(1)}"
        elif match := re.search(r"valve[-_ ]?(\d+)", lower):
            stem = f"Valve_{match.group(1)}"
        elif match := re.search(r"loop[-_ ]?(\d+)", lower):
            stem = f"Loop_{match.group(1)}"
        elif "main" in lower:
            stem = f"Main_{self._sanitize_name(unit_name)}"
        else:
            stem = self._sanitize_name(unit_name)

        candidate = stem
        suffix = 2
        while f"{candidate}.scl" in seen:
            candidate = f"{stem}_{suffix}"
            suffix += 1
        seen.add(f"{candidate}.scl")
        return f"{candidate}.scl"

    def _extract_program_blocks(self, raw_source: dict[str, str]) -> list[dict[str, str]]:
        start_pattern = re.compile(r"^\s*(PROGRAM|FUNCTION_BLOCK|FUNCTION)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
        end_tokens = {
            "PROGRAM": "END_PROGRAM",
            "FUNCTION_BLOCK": "END_FUNCTION_BLOCK",
            "FUNCTION": "END_FUNCTION",
        }

        blocks: list[dict[str, str]] = []
        for source_path, content in raw_source.items():
            lines = content.splitlines()
            in_block = False
            block_type = ""
            block_name = ""
            collected: list[str] = []

            for line in lines:
                if not in_block:
                    match = start_pattern.match(line)
                    if not match:
                        continue
                    block_type = match.group(1).upper()
                    block_name = match.group(2)
                    in_block = True
                    collected = [line]
                    continue

                collected.append(line)
                if line.strip().upper().startswith(end_tokens.get(block_type, "END")):
                    blocks.append(
                        {
                            "name": block_name,
                            "kind": block_type,
                            "content": "\n".join(collected).strip() + "\n",
                            "source_file": source_path,
                        }
                    )
                    in_block = False
                    block_type = ""
                    block_name = ""
                    collected = []

            if in_block and collected:
                blocks.append(
                    {
                        "name": block_name,
                        "kind": block_type,
                        "content": "\n".join(collected).strip() + "\n",
                        "source_file": source_path,
                    }
                )

        if blocks:
            return blocks

        fallback_content = next(iter(raw_source.values()), "")
        if fallback_content.strip():
            return [
                {
                    "name": "MainProgram",
                    "kind": "PROGRAM",
                    "content": fallback_content,
                    "source_file": next(iter(raw_source.keys()), "generated.st"),
                }
            ]
        return []

    @staticmethod
    def _extract_tags(raw_source: dict[str, str]) -> list[dict[str, str]]:
        declaration_pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^;]+);", re.MULTILINE)
        tag_pattern = re.compile(r"\b([A-Za-z]{1,6}[-_ ]?\d{1,5}[A-Za-z0-9]{0,4})\b")

        tags: dict[str, dict[str, str]] = {}
        for source_path, content in raw_source.items():
            for name, dtype in declaration_pattern.findall(content):
                if name not in tags:
                    tags[name] = {
                        "name": name,
                        "type": dtype.strip(),
                        "source": source_path,
                        "metadata": "variable_declaration",
                    }

            for candidate in tag_pattern.findall(content):
                normalized = candidate.replace(" ", "_").replace("-", "_")
                if normalized not in tags:
                    tags[normalized] = {
                        "name": normalized,
                        "type": "UNKNOWN",
                        "source": source_path,
                        "metadata": "tag_pattern",
                    }

        return sorted(tags.values(), key=lambda item: item["name"].lower())

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
                    "source": tag["source"],
                    "metadata": tag["metadata"],
                },
            )
        xml_payload = ET.tostring(root, encoding="unicode")
        return f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n{xml_payload}\n"

    def render_project(
        self,
        logic_model: dict[str, Any],
        output_root: Path,
        jinja_env: Environment,
    ) -> dict[str, Any]:
        _ = jinja_env
        project = logic_model.get("project", {})
        project_id = str(project.get("id") or "unknown-project")
        raw_source = logic_model.get("raw_source", {})
        if not isinstance(raw_source, dict):
            raw_source = {}

        tia_root = output_root / "TIA_Project"
        blocks_root = tia_root / "ProgramBlocks"
        tags_root = tia_root / "Tags"
        blocks_root.mkdir(parents=True, exist_ok=True)
        tags_root.mkdir(parents=True, exist_ok=True)

        blocks = self._extract_program_blocks({str(key): str(value) for key, value in raw_source.items()})
        seen_file_names: set[str] = set()
        generated_files: list[str] = []

        for block in blocks:
            file_name = self._unit_file_name(block["name"], seen_file_names)
            target = blocks_root / file_name
            target.write_text(block["content"], encoding="utf-8")
            generated_files.append(str(target.relative_to(output_root)))

        tags = self._extract_tags({str(key): str(value) for key, value in raw_source.items()})
        tags_xml = self._build_tags_xml(project_id=project_id, tags=tags)
        tags_file = tags_root / "plant_tags.xml"
        tags_file.write_text(tags_xml, encoding="utf-8")
        generated_files.append(str(tags_file.relative_to(output_root)))

        return {
            "files": sorted(generated_files),
            "metadata": {
                "block_count": len(blocks),
                "tag_count": len(tags),
                "project_structure": "TIA_Project/ProgramBlocks + TIA_Project/Tags",
            },
        }
