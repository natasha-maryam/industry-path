from __future__ import annotations

import json
import logging
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models.runtime_deploy import RuntimeDeployResponse, RuntimeDeployStep, RuntimeDeploySummary

from models.logic import IOMappingResult, RuntimeValidationResult, STGenerationResult
from services.io_mapping_engine import io_mapping_engine
from services.project_service import project_service


class RuntimeDeployer:
    """Runtime readiness hooks for OpenPLC payload validation."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _is_containerized_runtime() -> bool:
        return Path("/.dockerenv").exists() or os.getenv("RUNNING_IN_DOCKER", "").lower() in {"1", "true", "yes"}

    def _resolve_runtime_endpoint(self, runtime_config: dict[str, Any]) -> tuple[str, int, str]:
        target_runtime = str(runtime_config.get("target_runtime", "OpenPLC"))
        default_protocol = os.getenv("OPENPLC_PROTOCOL", "OpenPLC")
        protocol = str(runtime_config.get("protocol", default_protocol))

        if target_runtime.lower() == "openplc":
            default_host = os.getenv("OPENPLC_HOST", "openplc" if self._is_containerized_runtime() else "127.0.0.1")
            default_port = int(os.getenv("OPENPLC_PORT", "8080"))
            requested_host = str(runtime_config.get("ip_address", default_host)).strip() or default_host
            localhost_tokens = {"127.0.0.1", "localhost", "0.0.0.0"}
            if self._is_containerized_runtime() and requested_host.lower() in localhost_tokens:
                host = default_host
            else:
                host = requested_host
            port = int(runtime_config.get("port", default_port))
            return host, port, protocol

        default_host = str(runtime_config.get("ip_address", "127.0.0.1"))
        default_port = int(runtime_config.get("port", 8080))
        return default_host, default_port, protocol

    @staticmethod
    def _step(name: str, status: str, message: str) -> RuntimeDeployStep:
        return RuntimeDeployStep(name=name, status=status, message=message)

    @staticmethod
    def _resolve_workspace_root(project_id: str, workspace_path: str) -> Path:
        project_paths = project_service.workspace_paths(project_id)
        configured_root = Path(workspace_path).expanduser() if workspace_path else project_paths.root
        if configured_root.exists():
            return configured_root
        return project_paths.root

    @staticmethod
    def _collect_st_files(control_logic_root: Path) -> list[Path]:
        return sorted(
            [
                file
                for file in control_logic_root.rglob("*.st")
                if file.is_file() and file.stat().st_size > 0
            ]
        )

    @staticmethod
    def _load_latest_io_mapping(project_id: str, workspace_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
        warnings: list[str] = []
        latest = io_mapping_engine.get_latest_io_mapping(project_id)
        if latest:
            return list(latest.get("rows", [])), warnings

        fallback = workspace_root / "io_mapping" / "io_mapping_latest.json"
        if fallback.exists():
            payload = json.loads(fallback.read_text())
            warnings.append("Using filesystem IO mapping artifact because database version was not found.")
            return list(payload.get("rows", [])), warnings

        return [], warnings

    @staticmethod
    def _project_name(project_id: str) -> str:
        project = project_service.get_project(project_id)
        return project.name

    @staticmethod
    def _build_openplc_payload(
        project_id: str,
        project_name: str,
        st_files: list[Path],
        io_rows: list[dict[str, Any]],
        runtime_config: dict[str, Any],
        workspace_root: Path,
    ) -> dict[str, Any]:
        return {
            "project_id": project_id,
            "project_name": project_name,
            "runtime_target": runtime_config.get("target_runtime", "OpenPLC"),
            "protocol": runtime_config.get("protocol", "OpenPLC"),
            "ip_address": runtime_config.get("ip_address", "127.0.0.1"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace_path": str(workspace_root),
            "st_files": [
                {
                    "path": str(path.relative_to(workspace_root)),
                    "name": path.name,
                    "content": path.read_text(),
                }
                for path in st_files
            ],
            "io_points": io_rows,
        }

    @staticmethod
    def _runtime_connectivity_check(ip_address: str, port: int, timeout_seconds: float = 2.0) -> tuple[bool, str]:
        try:
            with socket.create_connection((ip_address, port), timeout=timeout_seconds):
                return True, f"Connected to runtime endpoint {ip_address}:{port}."
        except OSError as exc:
            return False, f"Could not connect to runtime endpoint {ip_address}:{port} ({exc})."

    def openplc_health(self) -> dict[str, Any]:
        host = os.getenv("OPENPLC_HOST", "openplc" if self._is_containerized_runtime() else "127.0.0.1")
        port = int(os.getenv("OPENPLC_PORT", "8080"))
        protocol = os.getenv("OPENPLC_PROTOCOL", "OpenPLC")

        socket_ok, socket_message = self._runtime_connectivity_check(host, port)
        http_status = "unknown"
        url = f"http://{host}:{port}/"
        try:
            request = urllib.request.Request(url=url, method="GET")
            with urllib.request.urlopen(request, timeout=2.0) as response:
                http_status = f"http_{response.status}"
        except urllib.error.URLError as exc:
            http_status = f"error: {exc.reason}"
        except Exception as exc:
            http_status = f"error: {exc}"

        return {
            "runtime": "OpenPLC",
            "protocol": protocol,
            "host": host,
            "port": port,
            "socket": "connected" if socket_ok else socket_message,
            "http": http_status,
            "status": "ok" if socket_ok else "error",
        }

    def deploy_to_runtime(self, project_id: str, workspace_path: str, runtime_config: dict) -> dict:
        """Deploy validated ST + IO mapping payload into OpenPLC runtime and return stepwise validation status."""

        project_service.ensure_project(project_id)
        errors: list[str] = []
        warnings: list[str] = []
        steps: list[RuntimeDeployStep] = []
        files_loaded = 0
        io_points_bound = 0

        workspace_root = self._resolve_workspace_root(project_id, workspace_path)
        control_logic_root = workspace_root / "control_logic"
        runtime_root = workspace_root / "runtime"
        runtime_target = str(runtime_config.get("target_runtime", "OpenPLC"))
        project_name = self._project_name(project_id)
        runtime_host, runtime_port, runtime_protocol = self._resolve_runtime_endpoint(runtime_config)

        if runtime_target.lower() != "openplc":
            warnings.append(f"Runtime target `{runtime_target}` is not fully implemented yet; using generic connectivity validation only.")

        openplc_project_dir = runtime_root / "openplc_project"
        st_import_dir = openplc_project_dir / "st_sources"

        try:
            openplc_project_dir.mkdir(parents=True, exist_ok=True)
            st_import_dir.mkdir(parents=True, exist_ok=True)
            steps.append(self._step("create_project", "passed", f"Prepared runtime project directory at {openplc_project_dir}."))
        except Exception as exc:
            message = f"Failed to prepare runtime project directory: {exc}"
            steps.append(self._step("create_project", "failed", message))
            errors.append(message)

        st_files = self._collect_st_files(control_logic_root)
        if errors:
            st_files = []

        if not st_files:
            message = f"No generated ST files found in {control_logic_root}."
            steps.append(self._step("import_st", "failed", message))
            errors.append(message)
        else:
            try:
                for source_file in st_files:
                    target_file = st_import_dir / source_file.name
                    target_file.write_text(source_file.read_text())
                files_loaded = len(st_files)
                steps.append(self._step("import_st", "passed", f"Imported {files_loaded} ST file(s) into runtime project."))
            except Exception as exc:
                message = f"Failed to import ST files: {exc}"
                steps.append(self._step("import_st", "failed", message))
                errors.append(message)

        io_rows, io_warnings = self._load_latest_io_mapping(project_id, workspace_root)
        warnings.extend(io_warnings)
        if not io_rows:
            message = "Validated IO mapping was not found for this project."
            steps.append(self._step("apply_io_config", "failed", message))
            errors.append(message)
        else:
            try:
                io_points_bound = len(io_rows)
                io_config_file = openplc_project_dir / "io_config.json"
                io_config_file.write_text(json.dumps({"io_points": io_rows}, indent=2))
                steps.append(self._step("apply_io_config", "passed", f"Applied IO configuration with {io_points_bound} point(s)."))
            except Exception as exc:
                message = f"Failed to apply IO configuration: {exc}"
                steps.append(self._step("apply_io_config", "failed", message))
                errors.append(message)

        if errors:
            steps.append(self._step("start_runtime", "failed", "Runtime start skipped because previous deployment steps failed."))
        else:
            ok, message = self._runtime_connectivity_check(runtime_host, runtime_port)

            if ok:
                runtime_config_enriched = {
                    **runtime_config,
                    "target_runtime": runtime_target,
                    "protocol": runtime_protocol,
                    "ip_address": runtime_host,
                    "port": runtime_port,
                }
                payload = self._build_openplc_payload(
                    project_id=project_id,
                    project_name=project_name,
                    st_files=st_files,
                    io_rows=io_rows,
                    runtime_config=runtime_config_enriched,
                    workspace_root=workspace_root,
                )
                payload_file = openplc_project_dir / "openplc_payload.json"
                payload_file.write_text(json.dumps(payload, indent=2))
                steps.append(self._step("start_runtime", "passed", f"{message} Protocol={runtime_protocol}"))
            else:
                steps.append(self._step("start_runtime", "failed", message))
                errors.append(message)

        response = RuntimeDeployResponse(
            status="passed" if len(errors) == 0 else "failed",
            summary=RuntimeDeploySummary(
                files_loaded=files_loaded,
                io_points_bound=io_points_bound,
                runtime_target=runtime_target,
                project_name=project_name,
            ),
            steps=steps,
            errors=errors,
            warnings=warnings,
        )

        runtime_report = runtime_root / "runtime_validation.json"
        runtime_report.write_text(json.dumps(response.model_dump(mode="json"), indent=2))
        self.logger.info("Runtime deployment completed: project=%s status=%s", project_id, response.status)
        return response.model_dump(mode="json")

    def validate_openplc_readiness(
        self,
        project_id: str,
        st_generation: STGenerationResult,
        io_mapping: IOMappingResult,
    ) -> RuntimeValidationResult:
        checks: list[str] = []
        details: list[str] = []

        checks.append("st_files_present")
        if not st_generation.files:
            details.append("No ST files were generated.")

        checks.append("io_mapping_present")
        if not io_mapping.channels:
            details.append("No IO channels are mapped.")

        checks.append("openplc_payload_scaffold")
        payload = {
            "project_id": project_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "st_files": [item.relative_path for item in st_generation.files],
            "io_channels": [item.model_dump() for item in io_mapping.channels],
            # TODO: Integrate real OpenPLC project import/export payload format.
            "todo": "OpenPLC runtime adapter integration pending.",
        }
        paths = project_service.workspace_paths(project_id)
        payload_file = paths.runtime / "openplc_payload.json"
        payload_file.write_text(json.dumps(payload, indent=2))

        status = "ready" if len(details) == 0 else "not_ready"
        result = RuntimeValidationResult(
            project_id=project_id,
            runtime="OpenPLC",
            status=status,
            checks=checks,
            details=details or ["Runtime payload scaffold created successfully."],
        )
        self.logger.info("Runtime validation completed: project=%s status=%s", project_id, status)
        return result


runtime_deployer = RuntimeDeployer()
