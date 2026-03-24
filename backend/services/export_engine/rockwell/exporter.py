from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..common import LogicModel, VendorExportResult
from ..vendor_base import BaseVendorExporter


class RockwellExporter(BaseVendorExporter):
    vendor_key = "rockwell"

    @staticmethod
    def _sanitize(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned or "Block"

    def export(self, output_root: Path, logic_model: LogicModel) -> VendorExportResult:
        # Spec-defined output: Studio5000_Project/{AOIs,Programs,Tags} and final Studio5000_L5X.xml
        root = output_root / "Studio5000_Project"
        aois_root = root / "AOIs"
        programs_root = root / "Programs"
        tags_root = root / "Tags"
        aois_root.mkdir(parents=True, exist_ok=True)
        programs_root.mkdir(parents=True, exist_ok=True)
        tags_root.mkdir(parents=True, exist_ok=True)

        generated_files: list[str] = []
        block_count = 0

        for block in logic_model.function_blocks:
            target = aois_root / f"{self._sanitize(block.name)}.st"
            target.write_text(block.content, encoding="utf-8")
            generated_files.append(str(target.relative_to(output_root)))
            block_count += 1

        ordered_programs = [*logic_model.equipment_routines, *logic_model.loops, *logic_model.programs, *logic_model.interlocks, *logic_model.alarms]
        for block in ordered_programs:
            target = programs_root / f"{self._sanitize(block.name)}.st"
            target.write_text(block.content, encoding="utf-8")
            generated_files.append(str(target.relative_to(output_root)))
            block_count += 1

        tag_xml_root = ET.Element("Tags")
        for tag in logic_model.tags:
            ET.SubElement(tag_xml_root, "Tag", attrib={"Name": tag.name, "DataType": tag.data_type, "Description": tag.metadata})
        tags_file = tags_root / "plant_tags.xml"
        tags_file.write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + ET.tostring(tag_xml_root, encoding="unicode") + "\n",
            encoding="utf-8",
        )
        generated_files.append(str(tags_file.relative_to(output_root)))

        l5x_root = ET.Element(
            "RSLogix5000Content",
            attrib={
                "SchemaRevision": "1.0",
                "SoftwareRevision": "32.00",
                "TargetName": logic_model.project_name,
                "TargetType": "Controller",
                "ContainsContext": "true",
                "Owner": logic_model.owner,
            },
        )
        controller = ET.SubElement(
            l5x_root,
            "Controller",
            attrib={
                "Use": "Target",
                "Name": logic_model.project_name,
                "ProcessorType": "1756-L83E",
                "MajorRev": "32",
                "MinorRev": "11",
            },
        )

        aois = ET.SubElement(controller, "AddOnInstructionDefinitions")
        for block in logic_model.function_blocks:
            ET.SubElement(aois, "AddOnInstructionDefinition", attrib={"Name": self._sanitize(block.name)})

        programs_node = ET.SubElement(controller, "Programs")
        for block in ordered_programs:
            ET.SubElement(programs_node, "Program", attrib={"Name": self._sanitize(block.name), "MainRoutineName": "MainRoutine"})

        tags_node = ET.SubElement(controller, "Tags")
        for tag in logic_model.tags:
            ET.SubElement(tags_node, "Tag", attrib={"Name": tag.name, "DataType": tag.data_type})

        artifact_path = output_root / "Studio5000_L5X.xml"
        artifact_path.write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + ET.tostring(l5x_root, encoding="unicode") + "\n",
            encoding="utf-8",
        )

        return VendorExportResult(
            artifact_name="Studio5000_L5X.xml",
            artifact_path=artifact_path,
            generated_files=sorted(generated_files + [str(artifact_path.relative_to(output_root))]),
            logic_block_count=block_count,
            tag_count=len(logic_model.tags),
            notes=["Rockwell import scaffold is XML/Jinja-style and intentionally minimal for open-source compatibility."],
        )
