from __future__ import annotations

import json
import zipfile
from pathlib import Path

from ..common import LogicModel, VendorExportResult
from ..vendor_base import BaseVendorExporter


class CodesysExporter(BaseVendorExporter):
    vendor_key = "codesys"

    def export(self, output_root: Path, logic_model: LogicModel) -> VendorExportResult:
        # Partially supported: stable internal structure packaged as zip (not emitted as .project until fully valid).
        root = output_root / "Codesys_Project"
        pou_root = root / "POUs"
        pou_root.mkdir(parents=True, exist_ok=True)

        generated_files: list[str] = []
        for block in [*logic_model.programs, *logic_model.function_blocks, *logic_model.equipment_routines, *logic_model.loops]:
            target = pou_root / f"{block.name}.st"
            target.write_text(block.content, encoding="utf-8")
            generated_files.append(str(target.relative_to(output_root)))

        gvl = root / "GlobalVariables.gvl"
        gvl.write_text(
            "VAR_GLOBAL\n" + "\n".join(f"  {tag.name}: {tag.data_type};" for tag in logic_model.tags) + "\nEND_VAR\n",
            encoding="utf-8",
        )
        generated_files.append(str(gvl.relative_to(output_root)))

        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "project": logic_model.project_name,
                    "vendor": "codesys",
                    "todo": "Replace scaffold package with fully valid Codesys .project generation when supported.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        generated_files.append(str(manifest.relative_to(output_root)))

        artifact = output_root / "Codesys_Project.zip"
        with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(root.rglob("*")):
                if file.is_file():
                    archive.write(file, arcname=str(file.relative_to(output_root)))

        return VendorExportResult(
            artifact_name="Codesys_Project.zip",
            artifact_path=artifact,
            generated_files=sorted(generated_files + [str(artifact.relative_to(output_root))]),
            logic_block_count=len(logic_model.programs) + len(logic_model.function_blocks) + len(logic_model.equipment_routines) + len(logic_model.loops),
            tag_count=len(logic_model.tags),
            notes=["Codesys .project not emitted because fully valid format support is pending; scaffold package generated."],
        )
