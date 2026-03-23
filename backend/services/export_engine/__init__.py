from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from services.project_service import project_service

from .common import STSourceFile
from .parser import build_logic_model
from .vendors import get_vendor_exporter


class ExportEngine:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def _load_st_files(self, project_id: str) -> list[STSourceFile]:
        paths = project_service.workspace_paths(project_id)
        st_files = sorted(paths.control_logic.rglob("*.st"))
        loaded: list[STSourceFile] = []
        for file in st_files:
            content = file.read_text(encoding="utf-8")
            loaded.append(
                STSourceFile(
                    path=str(file.relative_to(paths.control_logic)),
                    content=content,
                    lines=len(content.splitlines()),
                )
            )
        if not loaded:
            raise HTTPException(status_code=400, detail="No Structured Text files found in selected project /control_logic")
        return loaded

    @staticmethod
    def _utcnow_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _exports_root(self, project_id: str) -> Path:
        paths = project_service.workspace_paths(project_id)
        root = paths.root / "exports"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _normalize_name(value: str) -> str:
        return "_".join(part for part in value.strip().split() if part) or "project"

    def create_export(self, vendor: str, project_id: str) -> dict[str, object]:
        project = project_service.get_project(project_id)
        st_files = self._load_st_files(project_id)
        logic_model = build_logic_model(project_id=str(project.id), project_name=project.name, owner=project.owner, st_files=st_files)

        exporter = get_vendor_exporter(vendor)
        if exporter is None:
            raise HTTPException(status_code=400, detail=f"Unsupported export vendor: {vendor}")

        self._logger.info("export vendor_selected=%s project_id=%s", vendor, project_id)

        export_id = str(uuid4())
        exports_root = self._exports_root(project_id)
        run_root = exports_root / export_id
        run_root.mkdir(parents=True, exist_ok=True)

        if vendor.lower() == "siemens":
            vendor_root = exports_root / project_id
            tia_dir = vendor_root / "TIA_Project"
            if tia_dir.exists():
                shutil.rmtree(tia_dir)
            vendor_root.mkdir(parents=True, exist_ok=True)
            result = exporter.export(vendor_root, logic_model)
        else:
            result = exporter.export(run_root, logic_model)

        manifest = {
            "export_id": export_id,
            "project_id": project_id,
            "project_name": project.name,
            "vendor": vendor,
            "generated_at": self._utcnow_iso(),
            "files": result.generated_files,
            "package_path": str(result.artifact_path),
            "artifact_name": result.artifact_name,
            "logic_block_count": result.logic_block_count,
            "tag_count": result.tag_count,
            "notes": result.notes,
        }
        (run_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        self._logger.info(
            "export vendor=%s blocks=%s tags=%s artifact=%s",
            vendor,
            result.logic_block_count,
            result.tag_count,
            result.artifact_path,
        )

        return {
            "export_id": export_id,
            "project_id": project_id,
            "project_name": project.name,
            "vendor": vendor,
            "generated_at": manifest["generated_at"],
            "files": result.generated_files,
            "download_url": f"/api/exports/{export_id}/download",
            "package_path": str(result.artifact_path),
            "artifact_name": result.artifact_name,
            "logic_block_count": result.logic_block_count,
            "tag_count": result.tag_count,
        }

    def _find_export_manifest(self, export_id: str) -> tuple[Path, dict[str, object]]:
        projects_root = project_service.workspace_root
        for project_dir in projects_root.iterdir():
            if not project_dir.is_dir():
                continue
            run_root = project_dir / "exports" / export_id
            manifest_path = run_root / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return run_root, manifest
        raise HTTPException(status_code=404, detail=f"Export not found: {export_id}")

    def download_export(self, export_id: str) -> tuple[Path, str]:
        _, manifest = self._find_export_manifest(export_id)
        package = Path(str(manifest.get("package_path") or ""))
        if not package.exists():
            raise HTTPException(status_code=404, detail=f"Export artifact missing for {export_id}")
        return package, str(manifest.get("artifact_name") or package.name)

    def cleanup_export(self, export_id: str) -> None:
        run_root, _ = self._find_export_manifest(export_id)
        shutil.rmtree(run_root, ignore_errors=True)


export_engine = ExportEngine()
