from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Any

from runtime_engine.beremiz_adapter import BeremizAdapter
from runtime_engine.runtime_signal_state import runtime_signal_state
from runtime_engine.runtime_telemetry import runtime_telemetry
from services.io_mapping_engine import io_mapping_engine
from services.project_service import project_service


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
        self.logger.info(
            "runtime_manager deploy project_id=%s st_files=%s io_points=%s",
            project_id,
            len(resolved_st_files),
            len(effective_io_map),
        )

        runtime_signal_state.sync_project(project_id, io_rows=effective_io_map)
        steps: list[dict[str, Any]] = []
        errors: list[str] = []

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
                "status": "failed",
                "project_id": project_id,
                "runtime": "headless-matiec",
                "runtime_project_dir": None,
                "steps": steps,
                "errors": errors,
                "dependency_report": dependency_report,
            }

        prepared, prepared_message, project_dir = self.runtime.create_runtime_project(project_id, resolved_st_files)
        self._active_project_id = project_id
        self._active_project_dir = project_dir
        if not prepared:
            steps.append({"name": "compile_st", "status": "failed", "message": prepared_message})
            errors.append(prepared_message)

        if not errors:
            compile_ok, compile_step = self.runtime.compile_st(project_dir)
            steps.append(compile_step)
            if not compile_ok:
                errors.append(compile_step["message"])

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
            apply_ok, apply_step = self.runtime.apply_io(project_dir, effective_io_map)
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

        return {
            "status": "passed" if not errors else "failed",
            "project_id": project_id,
            "runtime": "headless-matiec",
            "runtime_project_dir": str(project_dir),
            "steps": steps,
            "errors": errors,
            "dependency_report": dependency_report,
            "runtime_status": self.runtime.runtime_status(),
        }

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
