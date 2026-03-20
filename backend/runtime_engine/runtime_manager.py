from __future__ import annotations

import logging
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime_engine.beremiz_adapter import BeremizAdapter
from runtime_engine.runtime_signal_state import runtime_signal_state
from runtime_engine.runtime_telemetry import runtime_telemetry
from services.io_mapping_engine import io_mapping_engine
from services.project_service import project_service
from services.st_codegen_utils import st_codegen_utils


class RuntimeManager:
    """Central runtime orchestration layer for deploy/start/stop workflow."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.runtime = BeremizAdapter()
        self._active_project_id: str | None = None
        self._active_project_dir: Path | None = None

    @staticmethod
    def _ensure_st_paths(st_files: list[str | Path]) -> list[Path]:
        paths = [Path(item).expanduser().resolve() for item in st_files]
        return [item for item in paths if item.exists() and item.is_file() and item.suffix.lower() == ".st"]

    def _collect_project_st_files(self, project_id: str) -> list[Path]:
        project_paths = project_service.workspace_paths(project_id)
        return sorted(
            [
                file
                for file in project_paths.control_logic.rglob("*.st")
                if file.is_file() and file.stat().st_size > 0
            ]
        )

    @staticmethod
    def _extract_global_signal_rows(st_files: list[Path]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        signal_type_by_st = {
            "REAL": "analog",
            "LREAL": "analog",
            "INT": "int",
            "DINT": "int",
            "BOOL": "digital",
        }

        declaration_block_pattern = re.compile(r"\b(VAR_EXTERNAL|VAR_GLOBAL)\b(.*?)\bEND_VAR\b", flags=re.S | re.I)
        declaration_pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)", flags=re.M)

        for st_file in st_files:
            content = st_file.read_text()
            for _, block in declaration_block_pattern.findall(content):
                for match in declaration_pattern.finditer(block):
                    tag = match.group(1).upper().strip()
                    st_type = match.group(2).upper().strip()
                    if not tag or tag in seen:
                        continue
                    seen.add(tag)
                    rows.append(
                        {
                            "tag": tag,
                            "io_type": "VIRTUAL",
                            "st_type": st_type,
                            "signal_type": signal_type_by_st.get(st_type, "analog"),
                            "is_input": True,
                        }
                    )
        return rows

    @staticmethod
    def _augment_command_dependency_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        augmented = list(rows)
        known_tags = {str(item.get("tag") or "").strip().upper() for item in augmented if str(item.get("tag") or "").strip()}

        additions: list[dict[str, Any]] = []
        for row in augmented:
            tag = str(row.get("tag") or "").strip().upper()
            if not tag:
                continue
            dependencies = st_codegen_utils.infer_command_dependencies(tag)
            if not dependencies:
                continue
            dependent_tags = [
                *dependencies.get("status_tags", []),
                *dependencies.get("fault_tags", []),
            ]
            for dependent in dependent_tags:
                dependent_tag = str(dependent or "").strip().upper()
                if not dependent_tag or dependent_tag in known_tags:
                    continue
                known_tags.add(dependent_tag)
                additions.append(
                    {
                        "tag": dependent_tag,
                        "io_type": "VIRTUAL",
                        "st_type": "BOOL",
                        "signal_type": "digital",
                        "is_input": True,
                    }
                )

        augmented.extend(additions)
        return augmented

    def _load_project_io_map(self, project_id: str) -> list[dict[str, Any]]:
        latest = io_mapping_engine.get_latest_io_mapping(project_id)
        if latest:
            return list(latest.get("rows", []))

        project_paths = project_service.workspace_paths(project_id)
        fallback = project_paths.io_mapping / "io_mapping_latest.json"
        if fallback.exists():
            payload = json.loads(fallback.read_text())
            return list(payload.get("rows", []))
        return []

    @staticmethod
    def _write_runtime_artifacts(project_id: str, payload: dict[str, Any], io_rows: list[dict[str, Any]]) -> str:
        runtime_dir = project_service.workspace_paths(project_id).runtime
        runtime_dir.mkdir(parents=True, exist_ok=True)
        deploy_payload_path = runtime_dir / "latest_deploy.json"
        io_payload_path = runtime_dir / "io_config.json"

        deploy_payload_path.write_text(json.dumps(payload, indent=2, default=str))
        io_payload_path.write_text(json.dumps(io_rows, indent=2, default=str))
        return str(runtime_dir)

    def deploy(
        self,
        project_id: str,
        st_files: list[str | Path] | None = None,
        io_map: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Deploy validated ST + IO map through headless matiec runtime flow."""

        supplied_st_files = st_files or []
        supplied_io_map = io_map or []
        resolved_st_files = self._ensure_st_paths(supplied_st_files) if supplied_st_files else self._collect_project_st_files(project_id)
        effective_io_map = supplied_io_map if supplied_io_map else self._load_project_io_map(project_id)
        global_signal_rows = self._extract_global_signal_rows(resolved_st_files)
        merged_catalog_rows = list(effective_io_map)
        merged_tags = {str(item.get("tag") or "").strip().upper() for item in merged_catalog_rows if str(item.get("tag") or "").strip()}
        for row in global_signal_rows:
            tag = str(row.get("tag") or "").strip().upper()
            if not tag or tag in merged_tags:
                continue
            merged_catalog_rows.append(row)
            merged_tags.add(tag)
        merged_catalog_rows = self._augment_command_dependency_rows(merged_catalog_rows)
        self.logger.info(
            "runtime_manager deploy project_id=%s st_files=%s io_points=%s",
            project_id,
            len(resolved_st_files),
            len(effective_io_map),
        )

        runtime_signal_state.sync_project(project_id, io_rows=merged_catalog_rows)
        steps: list[dict[str, Any]] = []
        errors: list[str] = []
        engineering_errors: list[dict[str, Any]] = []

        allowed_registry = {
            str(item.get("tag") or "").strip().upper()
            for item in merged_catalog_rows
            if str(item.get("tag") or "").strip()
        }
        runtime_snapshot = runtime_signal_state.get_project_snapshot(project_id)
        runtime_catalog = set(runtime_snapshot.get("current_values", {}).keys())

        dependency_report = self.runtime.dependency_report()
        if not dependency_report["ok"]:
            message = f"Runtime dependencies missing: {dependency_report['missing']}"
            errors.append(message)
            steps.extend(
                [
                    {"name": "compile_st", "status": "failed", "message": message},
                    {"name": "generate_c", "status": "failed", "message": "Skipped due to missing dependencies."},
                    {"name": "build_runtime", "status": "failed", "message": "Skipped due to missing dependencies."},
                    {"name": "apply_io", "status": "failed", "message": "Skipped due to missing dependencies."},
                    {"name": "start_runtime", "status": "failed", "message": "Skipped due to missing dependencies."},
                ]
            )
            return {
                "success": False,
                "status": "failed",
                "project_id": project_id,
                "runtime": "headless-matiec",
                "runtime_project_dir": None,
                "steps": steps,
                "errors": errors,
                "engineering_errors": engineering_errors,
                "dependency_report": dependency_report,
            }

        prepared, prepared_message, project_dir = self.runtime.create_runtime_project(project_id, resolved_st_files)
        self._active_project_id = project_id
        self._active_project_dir = project_dir
        if not prepared:
            steps.append({"name": "compile_st", "status": "failed", "message": prepared_message})
            errors.append(prepared_message)

        if not errors:
            compile_ok, compile_step = self.runtime.compile_st(
                project_dir,
                allowed_registry=allowed_registry,
                runtime_catalog=runtime_catalog,
            )
            steps.append(compile_step)
            if not compile_ok:
                errors.append(compile_step["message"])
                detail = compile_step.get("detail") if isinstance(compile_step, dict) else None
                if isinstance(detail, dict):
                    compile_engineering_errors = detail.get("engineering_errors")
                    if isinstance(compile_engineering_errors, list):
                        engineering_errors.extend([item for item in compile_engineering_errors if isinstance(item, dict)])

        if not errors:
            generate_ok, generate_step = self.runtime.generate_c(project_dir)
            steps.append(generate_step)
            if not generate_ok:
                errors.append(generate_step["message"])
        else:
            steps.append({"name": "generate_c", "status": "failed", "message": "Skipped because compile_st failed."})

        if not errors:
            build_ok, build_step = self.runtime.build_runtime(project_dir)
            steps.append(build_step)
            if not build_ok:
                errors.append(build_step["message"])
        else:
            steps.append({"name": "build_runtime", "status": "failed", "message": "Skipped because generate_c failed."})

        if not errors:
            apply_ok, apply_step = self.runtime.apply_io(project_dir, merged_catalog_rows)
            steps.append(apply_step)
            if not apply_ok:
                errors.append(apply_step["message"])
        else:
            steps.append({"name": "apply_io", "status": "failed", "message": "Skipped because build_runtime failed."})

        if not errors:
            start_ok, start_step = self.runtime.start_runtime(project_dir)
            steps.append(start_step)
            if not start_ok:
                errors.append(start_step["message"])
            else:
                runtime_telemetry.update_tag("RUNTIME_STATE", "RUNNING")
                runtime_telemetry.update_tag("RUNTIME_PROJECT", project_id)
                runtime_signal_state.sync_project(project_id)
        else:
            steps.append({"name": "start_runtime", "status": "failed", "message": "Skipped because apply_io failed."})

        response_payload = {
            "success": len(errors) == 0,
            "status": "passed" if not errors else "failed",
            "project_id": project_id,
            "runtime": "headless-matiec",
            "runtime_project_dir": str(project_dir),
            "steps": steps,
            "errors": errors,
            "engineering_errors": engineering_errors,
            "dependency_report": dependency_report,
            "runtime_status": self.runtime.runtime_status(),
            "target_runtime": "headless-matiec",
            "protocol": "BEREMIZ",
            "plc_address": None,
            "io_rows": merged_catalog_rows,
            "deployed_version": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        }

        artifact_root = self._write_runtime_artifacts(project_id, response_payload, merged_catalog_rows)
        response_payload["artifact_path"] = artifact_root
        return response_payload

    def start(self) -> dict[str, Any]:
        if not self._active_project_dir:
            return {"status": "failed", "message": "No runtime project has been deployed yet."}

        ok, result = self.runtime.start_runtime(self._active_project_dir)
        if ok:
            runtime_telemetry.update_tag("RUNTIME_STATE", "RUNNING")
            if self._active_project_id:
                runtime_signal_state.sync_project(self._active_project_id)
            return {"status": "passed", "step": result, "runtime_project_dir": str(self._active_project_dir)}
        return {"status": "failed", "step": result, "runtime_project_dir": str(self._active_project_dir)}

    def stop(self) -> dict[str, Any]:
        ok, result = self.runtime.stop_runtime()
        if ok:
            runtime_telemetry.update_tag("RUNTIME_STATE", "STOPPED")
            return {"status": "passed", "step": result}
        return {"status": "failed", "step": result}

    def restart(self) -> dict[str, Any]:
        stop_result = self.stop()
        if stop_result["status"] == "failed":
            return {
                "status": "failed",
                "message": f"Runtime restart failed at stop step: {stop_result['step']['message']}",
            }

        start_result = self.start()
        if start_result["status"] == "failed":
            return {
                "status": "failed",
                "message": f"Runtime restart failed at start step: {start_result['step']['message']}",
            }

        return {
            "status": "passed",
            "message": "Runtime restarted successfully.",
        }

    def status(self) -> dict[str, Any]:
        return {
            "status": "passed",
            "project_id": self._active_project_id,
            "runtime": self.runtime.runtime_status(),
            "tags": runtime_telemetry.get_all_tags(),
        }


runtime_manager = RuntimeManager()
