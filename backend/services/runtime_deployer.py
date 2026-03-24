from __future__ import annotations

import json
import logging
import os
import socket
import urllib.parse
import urllib.error
import urllib.request
import uuid
from http.cookiejar import CookieJar
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
    def _truncate(value: str, max_len: int = 220) -> str:
        compact = " ".join(value.split())
        if len(compact) <= max_len:
            return compact
        return f"{compact[:max_len]}..."

    @staticmethod
    def _response_indicates_failure(payload: str) -> bool:
        text = payload.lower()
        failure_tokens = (
            "failed",
            "failure",
            "error",
            "syntax error",
            "compile error",
            "compilation failed",
            "unable",
            "invalid",
            "exception",
        )
        return any(token in text for token in failure_tokens)

    @staticmethod
    def _response_requires_auth(payload: str) -> bool:
        text = payload.lower()
        auth_tokens = (
            "action=\"/login\"",
            "name=\"username\"",
            "name=\"password\"",
            "sign in",
            "login",
        )
        return any(token in text for token in auth_tokens)

    def _append_step(self, steps: list[RuntimeDeployStep], name: str, status: str, message: str) -> None:
        steps.append(self._step(name, status, message))
        log_method = self.logger.info if status == "passed" else self.logger.warning
        log_method("runtime_deploy step=%s status=%s detail=%s", name, status, message)

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

    @staticmethod
    def _build_single_st_bundle(project_name: str, st_files: list[Path]) -> str:
        header = [
            f"(* CrossLayerX OpenPLC bundle for {project_name} *)",
            f"(* Generated at {datetime.now(timezone.utc).isoformat()} *)",
            "",
        ]
        body: list[str] = []
        for st_file in st_files:
            body.append(f"(* SOURCE: {st_file.name} *)")
            body.append(st_file.read_text())
            body.append("")
        return "\n".join(header + body)

    @staticmethod
    def _encode_multipart_formdata(fields: dict[str, str], file_field: str, file_name: str, file_content: str) -> tuple[bytes, str]:
        boundary = f"----crosslayerx-{uuid.uuid4().hex}"
        chunks: list[bytes] = []

        for key, value in fields.items():
            chunks.append(f"--{boundary}\r\n".encode("utf-8"))
            chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
            chunks.append(value.encode("utf-8"))
            chunks.append(b"\r\n")

        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"\r\n'.encode("utf-8")
        )
        chunks.append(b"Content-Type: text/plain\r\n\r\n")
        chunks.append(file_content.encode("utf-8"))
        chunks.append(b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(chunks), boundary

    def _http_request(
        self,
        method: str,
        url: str,
        timeout_seconds: float,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, int, str]:
        request = urllib.request.Request(url=url, method=method, data=data)
        for key, value in (headers or {}).items():
            request.add_header(key, value)

        try:
            open_fn = opener.open if opener is not None else urllib.request.urlopen
            with open_fn(request, timeout=timeout_seconds) as response:
                content = response.read().decode("utf-8", errors="ignore")
                return True, int(response.status), content
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
            return False, int(exc.code), payload
        except Exception as exc:
            return False, 0, str(exc)

    def _openplc_establish_session(
        self,
        runtime_host: str,
        runtime_port: int,
        runtime_config: dict[str, Any],
    ) -> tuple[urllib.request.OpenerDirector | None, bool, str]:
        username = str(runtime_config.get("username") or os.getenv("OPENPLC_USERNAME", "")).strip()
        password = str(runtime_config.get("password") or os.getenv("OPENPLC_PASSWORD", "")).strip()
        if not username or not password:
            return None, False, "OpenPLC credentials not configured; proceeding unauthenticated."

        login_url = f"http://{runtime_host}:{runtime_port}/login"
        cookie_jar = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

        ok, status_code, login_page = self._http_request(
            method="GET",
            url=login_url,
            timeout_seconds=6.0,
            opener=opener,
        )
        if not ok:
            return None, False, f"OpenPLC login page request failed (HTTP {status_code}): {self._truncate(login_page)}"

        form_payload = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
        ok, status_code, login_submit = self._http_request(
            method="POST",
            url=login_url,
            timeout_seconds=8.0,
            data=form_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            opener=opener,
        )
        if not ok:
            return None, False, f"OpenPLC login submission failed (HTTP {status_code}): {self._truncate(login_submit)}"
        if self._response_requires_auth(login_submit) or self._response_indicates_failure(login_submit):
            return None, False, f"OpenPLC login appears unsuccessful: {self._truncate(login_submit)}"

        ok, status_code, home_payload = self._http_request(
            method="GET",
            url=f"http://{runtime_host}:{runtime_port}/",
            timeout_seconds=6.0,
            opener=opener,
        )
        if not ok:
            return None, False, f"OpenPLC post-login verification failed (HTTP {status_code}): {self._truncate(home_payload)}"
        if self._response_requires_auth(home_payload):
            return None, False, "OpenPLC post-login verification still shows login page; credentials may be invalid."

        return opener, True, f"Authenticated OpenPLC session established for user `{username}`."

    def _openplc_verify_http_session(
        self,
        runtime_host: str,
        runtime_port: int,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, str]:
        ok, status_code, payload = self._http_request(
            method="GET",
            url=f"http://{runtime_host}:{runtime_port}/",
            timeout_seconds=5.0,
            opener=opener,
        )
        if ok and self._response_requires_auth(payload):
            return False, "OpenPLC reachable, but HTTP session is unauthenticated (redirect/login page detected)."
        if ok:
            return True, f"OpenPLC HTTP session reachable (GET / -> HTTP {status_code})."
        if status_code in {401, 403}:
            return False, f"OpenPLC reachable but HTTP auth blocked access to / (HTTP {status_code})."
        reason = self._truncate(payload) if payload else "no response body"
        return False, f"OpenPLC HTTP session check failed (HTTP {status_code}): {reason}"

    def _openplc_try_upload_project(
        self,
        runtime_host: str,
        runtime_port: int,
        project_name: str,
        bundled_st_content: str,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, str, str]:
        timeout_seconds = 8.0
        upload_paths = [
            "/upload-program",
            "/upload",
            "/api/program/upload",
            "/api/upload-program",
        ]
        file_fields = ["program_file", "file", "st_file", "program"]
        text_fields_sets = [
            {"project_name": project_name},
            {"name": project_name},
            {},
        ]
        attempts: list[str] = []
        auth_blocked = False

        for path in upload_paths:
            url = f"http://{runtime_host}:{runtime_port}{path}"
            for file_field in file_fields:
                for text_fields in text_fields_sets:
                    payload, boundary = self._encode_multipart_formdata(
                        fields=text_fields,
                        file_field=file_field,
                        file_name=f"{project_name}.st",
                        file_content=bundled_st_content,
                    )
                    ok, status_code, response_text = self._http_request(
                        method="POST",
                        url=url,
                        timeout_seconds=timeout_seconds,
                        data=payload,
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                        opener=opener,
                    )
                    excerpt = self._truncate(response_text)
                    attempts.append(
                        f"POST {path} field={file_field} params={list(text_fields.keys()) or ['none']} -> "
                        f"HTTP {status_code} {'ok' if ok else 'error'}; body='{excerpt}'"
                    )
                    if ok:
                        if self._response_requires_auth(response_text):
                            auth_blocked = True
                            continue
                        if self._response_indicates_failure(response_text):
                            continue
                        return (
                            True,
                            path,
                            f"OpenPLC upload accepted at {path} (HTTP {status_code}). Response: {excerpt or 'empty body'}",
                        )
                    if status_code not in {404, 405} and response_text:
                        self.logger.debug("OpenPLC upload attempt failed at %s (%s): %s", path, status_code, response_text[:200])

        details = " | ".join(attempts[-6:])
        if auth_blocked:
            return False, "", f"OpenPLC upload blocked by authentication (login required). Attempts: {details or 'none'}"
        return False, "", f"OpenPLC upload rejected/undetected. Attempts: {details or 'none'}"

    def _openplc_try_compile_load(
        self,
        runtime_host: str,
        runtime_port: int,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, str]:
        timeout_seconds = 10.0
        compile_candidates = [
            ("POST", "/compile-program"),
            ("POST", "/api/program/compile"),
            ("POST", "/api/compile"),
            ("GET", "/compile-program"),
        ]
        attempts: list[str] = []
        auth_blocked = False

        for method, path in compile_candidates:
            url = f"http://{runtime_host}:{runtime_port}{path}"
            ok, status_code, response_text = self._http_request(
                method=method,
                url=url,
                timeout_seconds=timeout_seconds,
                opener=opener,
            )
            excerpt = self._truncate(response_text)
            attempts.append(f"{method} {path} -> HTTP {status_code} {'ok' if ok else 'error'}; body='{excerpt}'")
            if ok:
                if self._response_requires_auth(response_text):
                    auth_blocked = True
                    continue
                if self._response_indicates_failure(response_text):
                    continue
                return True, f"Compile/load accepted via {path} (HTTP {status_code}). Response: {excerpt or 'empty body'}"

        if auth_blocked:
            return False, f"OpenPLC compile/load blocked by authentication (login required). Attempts: {' | '.join(attempts[-6:])}"
        return False, f"OpenPLC compile/load failed or endpoint unsupported. Attempts: {' | '.join(attempts[-6:])}"

    def _openplc_try_apply_io_mapping(
        self,
        runtime_host: str,
        runtime_port: int,
        io_rows: list[dict[str, Any]],
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, str]:
        timeout_seconds = 8.0
        mapping_payload = json.dumps({"io_points": io_rows}).encode("utf-8")
        mapping_candidates = [
            "/api/io-mapping",
            "/api/runtime/io",
            "/api/io",
            "/apply-io-config",
        ]
        attempts: list[str] = []
        auth_blocked = False

        for path in mapping_candidates:
            url = f"http://{runtime_host}:{runtime_port}{path}"
            ok, status_code, response_text = self._http_request(
                method="POST",
                url=url,
                timeout_seconds=timeout_seconds,
                data=mapping_payload,
                headers={"Content-Type": "application/json"},
                opener=opener,
            )
            excerpt = self._truncate(response_text)
            attempts.append(f"POST {path} -> HTTP {status_code} {'ok' if ok else 'error'}; body='{excerpt}'")
            if ok:
                if self._response_requires_auth(response_text):
                    auth_blocked = True
                    continue
                if self._response_indicates_failure(response_text):
                    continue
                return True, f"IO mapping applied via {path} (HTTP {status_code}). Response: {excerpt or 'empty body'}"

        if auth_blocked:
            return False, f"OpenPLC IO mapping blocked by authentication (login required). Attempts: {' | '.join(attempts[-6:])}"
        return False, f"OpenPLC IO mapping failed or endpoint unsupported. Attempts: {' | '.join(attempts[-6:])}"

    def _openplc_try_start_runtime(
        self,
        runtime_host: str,
        runtime_port: int,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, str]:
        timeout_seconds = 8.0
        start_candidates = [
            ("POST", "/start_plc"),
            ("POST", "/api/runtime/start"),
            ("POST", "/api/start"),
            ("GET", "/start_plc"),
        ]
        attempts: list[str] = []
        auth_blocked = False

        for method, path in start_candidates:
            url = f"http://{runtime_host}:{runtime_port}{path}"
            ok, status_code, response_text = self._http_request(
                method=method,
                url=url,
                timeout_seconds=timeout_seconds,
                opener=opener,
            )
            excerpt = self._truncate(response_text)
            attempts.append(f"{method} {path} -> HTTP {status_code} {'ok' if ok else 'error'}; body='{excerpt}'")
            if ok:
                if self._response_requires_auth(response_text):
                    auth_blocked = True
                    continue
                if self._response_indicates_failure(response_text):
                    continue
                return True, f"OpenPLC runtime start triggered via {path} (HTTP {status_code}). Response: {excerpt or 'empty body'}"

        if auth_blocked:
            return False, f"OpenPLC runtime start blocked by authentication (login required). Attempts: {' | '.join(attempts[-6:])}"
        return False, f"OpenPLC runtime start failed or endpoint unsupported. Attempts: {' | '.join(attempts[-6:])}"

    def _openplc_verify_loaded_program(
        self,
        runtime_host: str,
        runtime_port: int,
        expected_project_name: str,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> tuple[bool, str, str | None]:
        verification_paths = ["/", "/programs", "/dashboard", "/api/program"]
        expected_token = expected_project_name.strip().lower()
        attempts: list[str] = []

        for path in verification_paths:
            url = f"http://{runtime_host}:{runtime_port}{path}"
            ok, status_code, response_text = self._http_request(
                method="GET",
                url=url,
                timeout_seconds=5.0,
                opener=opener,
            )
            if not ok:
                attempts.append(f"GET {path} -> HTTP {status_code} error")
                continue

            normalized = response_text.lower()
            attempts.append(f"GET {path} -> HTTP {status_code} ok")
            if "blank program" in normalized:
                return False, f"OpenPLC reports Blank Program at {path} after deploy.", None
            if expected_token and expected_token in normalized:
                return True, f"Verified OpenPLC loaded generated project `{expected_project_name}` via {path} (HTTP {status_code}).", expected_project_name

        return False, f"Could not verify generated project name in OpenPLC program view. Checks: {' | '.join(attempts)}", None

    def deploy_to_runtime(self, project_id: str, workspace_path: str, runtime_config: dict) -> dict:
        """Deploy ST + IO mappings into OpenPLC and only pass when generated logic is verifiably loaded."""

        project_service.ensure_project(project_id)
        errors: list[str] = []
        warnings: list[str] = []
        steps: list[RuntimeDeployStep] = []
        files_loaded = 0
        io_points_bound = 0
        loaded_program_name: str | None = None
        openplc_integration_mode: str = "active"

        workspace_root = self._resolve_workspace_root(project_id, workspace_path)
        control_logic_root = workspace_root / "control_logic"
        runtime_root = workspace_root / "runtime"
        runtime_target = str(runtime_config.get("target_runtime", "OpenPLC"))
        project_name = self._project_name(project_id)
        runtime_host, runtime_port, runtime_protocol = self._resolve_runtime_endpoint(runtime_config)

        if runtime_target.lower() != "openplc":
            warnings.append(f"Runtime target `{runtime_target}` is not fully implemented yet; using generic connectivity validation only.")
            openplc_integration_mode = "partial"

        openplc_project_dir = runtime_root / "openplc_project"
        st_import_dir = openplc_project_dir / "st_sources"
        openplc_opener: urllib.request.OpenerDirector | None = None

        runtime_ok, runtime_message = self._runtime_connectivity_check(runtime_host, runtime_port)
        if runtime_ok:
            self._append_step(steps, "runtime_connected", "passed", runtime_message)
            openplc_opener, auth_ok, auth_message = self._openplc_establish_session(runtime_host, runtime_port, runtime_config)
            http_ok, http_message = self._openplc_verify_http_session(runtime_host, runtime_port, opener=openplc_opener)
            if not auth_ok:
                openplc_integration_mode = "partial"
                warnings.append(auth_message)
            if not http_ok:
                openplc_integration_mode = "partial"
                warnings.append(http_message)
            self.logger.info("runtime_deploy openplc_session auth_ok=%s http_ok=%s detail=%s | %s", auth_ok, http_ok, auth_message, http_message)
        else:
            self._append_step(steps, "runtime_connected", "failed", runtime_message)
            errors.append(runtime_message)

        try:
            openplc_project_dir.mkdir(parents=True, exist_ok=True)
            st_import_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            message = f"Failed to prepare runtime project directory: {exc}"
            errors.append(message)

        st_files = self._collect_st_files(control_logic_root)

        if not st_files:
            directory_exists = control_logic_root.exists()
            sample_entries = []
            if directory_exists:
                sample_entries = sorted([entry.name for entry in control_logic_root.iterdir()])[:10]
            message = (
                f"No generated ST files found in {control_logic_root}. "
                f"directory_exists={directory_exists}; sample_entries={sample_entries}"
            )
            self._append_step(steps, "project_uploaded", "failed", message)
            errors.append(message)
        else:
            try:
                for source_file in st_files:
                    target_file = st_import_dir / source_file.name
                    target_file.write_text(source_file.read_text())
                files_loaded = len(st_files)
                self.logger.info(
                    "runtime_deploy st_artifacts discovered=%s root=%s files=%s",
                    files_loaded,
                    control_logic_root,
                    [file.name for file in st_files],
                )
            except Exception as exc:
                message = f"Failed to import ST files: {exc}"
                errors.append(message)

        if errors:
            self._append_step(steps, "project_uploaded", "failed", "Project upload skipped because local preparation failed.")
        else:
            bundled_st = self._build_single_st_bundle(project_name=project_name, st_files=st_files)
            uploaded, upload_path, upload_message = self._openplc_try_upload_project(
                runtime_host=runtime_host,
                runtime_port=runtime_port,
                project_name=project_name,
                bundled_st_content=bundled_st,
                opener=openplc_opener,
            )

            if uploaded:
                self._append_step(steps, "project_uploaded", "passed", upload_message)
                self.logger.info("OpenPLC project upload completed for %s via %s", project_id, upload_path)
            else:
                openplc_integration_mode = "partial"
                message = (
                    f"{upload_message} Runtime is reachable, but generated project upload could not be confirmed. "
                    "Deployment is treated as failed to avoid false success on Blank Program."
                )
                warnings.append("OpenPLC integration appears partial: upload endpoint handshake failed.")
                self._append_step(steps, "project_uploaded", "failed", message)
                errors.append(message)

        if errors:
            self._append_step(steps, "logic_loaded", "failed", "Logic load skipped because runtime/project upload prerequisites failed.")
        else:
            missing_artifacts = [file.name for file in st_files if not file.exists()]
            if missing_artifacts:
                message = f"Logic load blocked: generated ST artifacts disappeared before compile/load: {missing_artifacts}"
                self._append_step(steps, "logic_loaded", "failed", message)
                errors.append(message)
            else:
                self.logger.info("runtime_deploy logic_loaded precheck st_files=%s", [file.name for file in st_files])

            if not errors:
                compile_ok, compile_message = self._openplc_try_compile_load(
                    runtime_host=runtime_host,
                    runtime_port=runtime_port,
                    opener=openplc_opener,
                )
                if not compile_ok:
                    openplc_integration_mode = "partial"
                    self._append_step(steps, "logic_loaded", "failed", compile_message)
                    errors.append(compile_message)
                    warnings.append("OpenPLC integration appears partial: compile/load endpoint handshake failed.")
                else:
                    verified, verify_message, loaded_name = self._openplc_verify_loaded_program(
                        runtime_host=runtime_host,
                        runtime_port=runtime_port,
                        expected_project_name=project_name,
                        opener=openplc_opener,
                    )
                    if verified:
                        loaded_program_name = loaded_name
                        self._append_step(steps, "logic_loaded", "passed", verify_message)
                    else:
                        self._append_step(steps, "logic_loaded", "failed", verify_message)
                        errors.append(verify_message)

        io_rows, io_warnings = self._load_latest_io_mapping(project_id, workspace_root)
        warnings.extend(io_warnings)
        if errors:
            self._append_step(steps, "io_applied", "failed", "IO apply skipped because generated logic did not load successfully.")
        elif not io_rows:
            message = "Validated IO mapping was not found for this project."
            self._append_step(steps, "io_applied", "failed", message)
            errors.append(message)
        else:
            try:
                io_points_bound = len(io_rows)
                io_config_file = openplc_project_dir / "io_config.json"
                io_config_file.write_text(json.dumps({"io_points": io_rows}, indent=2))
            except Exception as exc:
                message = f"Failed to prepare IO configuration artifact: {exc}"
                self._append_step(steps, "io_applied", "failed", message)
                errors.append(message)

        if not errors and io_rows:
            mapping_applied, mapping_message = self._openplc_try_apply_io_mapping(
                runtime_host=runtime_host,
                runtime_port=runtime_port,
                io_rows=io_rows,
                opener=openplc_opener,
            )
            if mapping_applied:
                self._append_step(steps, "io_applied", "passed", mapping_message)
            else:
                openplc_integration_mode = "partial"
                self._append_step(steps, "io_applied", "failed", mapping_message)
                errors.append(mapping_message)
                warnings.append("OpenPLC integration appears partial: IO mapping endpoint handshake failed.")

        if errors:
            self._append_step(steps, "runtime_started", "failed", "Runtime start skipped because logic load or IO apply did not complete.")
        else:
            started, started_message = self._openplc_try_start_runtime(
                runtime_host=runtime_host,
                runtime_port=runtime_port,
                opener=openplc_opener,
            )
            if started:
                self._append_step(steps, "runtime_started", "passed", f"{started_message} Protocol={runtime_protocol}")
            else:
                openplc_integration_mode = "partial"
                self._append_step(steps, "runtime_started", "failed", started_message)
                errors.append(started_message)
                warnings.append("OpenPLC integration appears partial: runtime start endpoint handshake failed.")

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

        response = RuntimeDeployResponse(
            status="passed" if len(errors) == 0 else "failed",
            summary=RuntimeDeploySummary(
                files_loaded=files_loaded,
                io_points_bound=io_points_bound,
                runtime_target=runtime_target,
                project_name=project_name,
                loaded_program_name=loaded_program_name,
                openplc_integration_mode="active" if openplc_integration_mode == "active" else "partial",
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
