from __future__ import annotations

import json
import zipfile
from pathlib import Path

from ..common import LogicModel, VendorExportResult
from ..vendor_base import BaseVendorExporter


class BeckhoffExporter(BaseVendorExporter):
    vendor_key = "beckhoff"

    def export(self, output_root: Path, logic_model: LogicModel) -> VendorExportResult:
        # Scaffold for later TwinCAT refinement (explicitly not full proprietary output yet).
        root = output_root / "TwinCAT_Project"
        pous = root / "POUs"
        fb_root = root / "FBs"
        gvl_root = root / "GVLs"
        pous.mkdir(parents=True, exist_ok=True)
        fb_root.mkdir(parents=True, exist_ok=True)
        gvl_root.mkdir(parents=True, exist_ok=True)

        generated_files: list[str] = []
        for block in logic_model.programs:
            file = pous / f"{block.name}.TcPOU"
            file.write_text(block.content, encoding="utf-8")
            generated_files.append(str(file.relative_to(output_root)))
        for block in logic_model.function_blocks:
            file = fb_root / f"{block.name}.TcPOU"
            file.write_text(block.content, encoding="utf-8")
            generated_files.append(str(file.relative_to(output_root)))

        gvl = gvl_root / "PlantTags.TcGVL"
        gvl.write_text("\n".join(f"{t.name}: {t.data_type};" for t in logic_model.tags), encoding="utf-8")
        generated_files.append(str(gvl.relative_to(output_root)))

        meta = root / "project_metadata.json"
        meta.write_text(json.dumps({"project": logic_model.project_name, "vendor": "beckhoff", "mode": "scaffold"}, indent=2), encoding="utf-8")
        generated_files.append(str(meta.relative_to(output_root)))

        artifact = output_root / "TwinCAT_Project.zip"
        with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(root.rglob("*")):
                if file.is_file():
                    archive.write(file, arcname=str(file.relative_to(output_root)))

        return VendorExportResult(
            artifact_name="TwinCAT_Project.zip",
            artifact_path=artifact,
            generated_files=sorted(generated_files + [str(artifact.relative_to(output_root))]),
            logic_block_count=len(logic_model.programs) + len(logic_model.function_blocks),
            tag_count=len(logic_model.tags),
            notes=["Beckhoff TwinCAT output is scaffolded for refinement in later phases."],
        )
