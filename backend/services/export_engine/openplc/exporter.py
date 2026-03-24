from __future__ import annotations

import json
import zipfile
from pathlib import Path

from ..common import LogicModel, VendorExportResult
from ..vendor_base import BaseVendorExporter


class OpenPLCExporter(BaseVendorExporter):
    vendor_key = "openplc"

    def export(self, output_root: Path, logic_model: LogicModel) -> VendorExportResult:
        # Scaffolded open-source runtime-friendly package for OpenPLC.
        root = output_root / "OpenPLC_Project"
        logic_root = root / "logic"
        vars_root = root / "variables"
        logic_root.mkdir(parents=True, exist_ok=True)
        vars_root.mkdir(parents=True, exist_ok=True)

        generated_files: list[str] = []
        combined = logic_root / "openplc_logic.st"
        combined.write_text(
            "\n\n".join(block.content for block in [*logic_model.programs, *logic_model.function_blocks, *logic_model.equipment_routines, *logic_model.loops]),
            encoding="utf-8",
        )
        generated_files.append(str(combined.relative_to(output_root)))

        vars_file = vars_root / "plant_variables.json"
        vars_file.write_text(
            json.dumps([{"name": t.name, "type": t.data_type, "metadata": t.metadata} for t in logic_model.tags], indent=2),
            encoding="utf-8",
        )
        generated_files.append(str(vars_file.relative_to(output_root)))

        manifest = root / "runtime_manifest.json"
        manifest.write_text(json.dumps({"runtime": "openplc", "project": logic_model.project_name, "mode": "scaffold"}, indent=2), encoding="utf-8")
        generated_files.append(str(manifest.relative_to(output_root)))

        artifact = output_root / "OpenPLC_Project.zip"
        with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(root.rglob("*")):
                if file.is_file():
                    archive.write(file, arcname=str(file.relative_to(output_root)))

        return VendorExportResult(
            artifact_name="OpenPLC_Project.zip",
            artifact_path=artifact,
            generated_files=sorted(generated_files + [str(artifact.relative_to(output_root))]),
            logic_block_count=len(logic_model.programs) + len(logic_model.function_blocks) + len(logic_model.equipment_routines) + len(logic_model.loops),
            tag_count=len(logic_model.tags),
            notes=["OpenPLC package is scaffolded and intended for iterative runtime integration."],
        )
