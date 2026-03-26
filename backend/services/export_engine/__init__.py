from __future__ import annotations

import json
import logging
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

from models.export import ExportVendor
from runtime_engine.runtime_manager import runtime_manager
from services.control_loop_store import control_loop_store
from services.logic_service import logic_service
from services.project_service import project_service
from services.version_manager import version_manager

from .common import LogicModel, STSourceFile, VendorExportResult
from .parser import build_logic_model
from .vendors import get_vendor_exporter


class ExportEngine:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def _normalize_tag_name(tag: str | None) -> str:
        return (tag or "").strip().upper()

    @classmethod
    def _is_internal_control_tag(cls, tag: str | None) -> bool:
        normalized = cls._normalize_tag_name(tag)
        if not normalized:
            return False

        internal_suffixes = (
            "_SP",
            "_HI_SP",
            "_HH_SP",
            "_LO_SP",
            "_LL_SP",
            "_STATUS",
            "_CMD",
            "_OUT",
            "_LTERM",
            "_ITERM",
            "_DTERM",
        )
        if normalized.endswith(internal_suffixes):
            return True

        if normalized.startswith("DT_LOOP_"):
            return True

        internal_tokens = ("CONTROL", "INTERNAL", "INTERLOCK", "DERIVED", "MODE", "STATE", "LTERM", "ITERM", "DTERM")
        return any(token in normalized for token in internal_tokens)

    @staticmethod
    def _looks_like_hardware_endpoint(tag: str | None) -> bool:
        normalized = (tag or "").strip().upper()
        if not normalized:
            return False
        hardware_patterns = (
            r"^(AIT|DPIT|FIT|LIT|PIT|TIT|FT|PT|LT|TT|LSH|LSL|PSH|PSL|TSH|TSL)[-_].+",
            r"^(FCV|PCV|LCV|TCV|XV|PMP|PUMP|VALVE|MTR|MOTOR|BLOWER|VFD)[-_].+",
        )
        return any(re.match(pattern, normalized) for pattern in hardware_patterns)

    @classmethod
    def _resolve_parent_base_tag(cls, tag: str | None) -> str | None:
        normalized = cls._normalize_tag_name(tag)
        if not normalized:
            return None

        candidate = normalized
        if candidate.startswith("ALM_"):
            candidate = candidate[4:]

        candidate = re.sub(
            r"(_HI|_LO|_HH|_HL|_LL|_ALM|_ALARM|_HI_ALARM|_LO_ALARM|_HH_ALARM|_LL_ALARM|_STATUS|_CMD)$",
            "",
            candidate,
        )

        candidate = candidate.replace("-", "_")
        match = re.search(
            r"(AIT|DPIT|FIT|LIT|PIT|TIT|FT|PT|LT|TT|FCV|PCV|LCV|TCV|XV|PMP|PUMP|VALVE|MTR|MOTOR|BLOWER|VFD)[_]?[0-9]{1,6}[A-Z0-9_]*",
            candidate,
        )
        if not match:
            return None

        return match.group(0)

    @classmethod
    def is_physical_io_tag(cls, tag: str | None, physical_candidates: set[str] | None = None) -> bool:
        normalized = cls._normalize_tag_name(tag)
        if not normalized:
            return False

        if cls._is_internal_control_tag(normalized):
            return False

        if "_ALM_" in normalized or normalized.endswith(("_ALM", "_ALARM")):
            return False

        looks_hardware = cls._looks_like_hardware_endpoint(normalized)
        if not looks_hardware and physical_candidates is None:
            return False

        if physical_candidates is not None and normalized not in physical_candidates:
            return False

        return True

    @classmethod
    def isPhysicalIOTag(cls, tag: str | None, physical_candidates: set[str] | None = None) -> bool:
        return cls.is_physical_io_tag(tag, physical_candidates)

    @classmethod
    def isPhysicalTag(cls, tag: str | None, physical_candidates: set[str] | None = None) -> bool:
        return cls.is_physical_io_tag(tag, physical_candidates)

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

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned or "artifact"

    @staticmethod
    def _extract_tag_tokens(content: str) -> set[str]:
        pattern = re.compile(r"\b[A-Za-z][A-Za-z0-9_]{2,}\b")
        return {item for item in pattern.findall(content)}

    @staticmethod
    def _safe_dict(value: object) -> dict[str, object]:
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            return dumped if isinstance(dumped, dict) else {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _safe_list(value: object) -> list[dict[str, object]]:
        if isinstance(value, list):
            normalized: list[dict[str, object]] = []
            for item in value:
                if hasattr(item, "model_dump"):
                    dumped = item.model_dump()
                    normalized.append(dumped if isinstance(dumped, dict) else {})
                elif isinstance(item, dict):
                    normalized.append(item)
            return normalized
        return []

    def _resolve_source_version(self, project_id: str, source_mode: str, source_version_id: str | None) -> tuple[str, str | None]:
        if source_mode != "version":
            return "live", None
        version_tag = (source_version_id or "").strip()
        if not version_tag:
            raise HTTPException(status_code=400, detail="source_version_id is required when source_mode is 'version'")
        record = version_manager.get_version(project_id, version_tag)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Version not found: {version_tag}")
        return "version", str(record.get("version_tag") or version_tag)

    def _build_readiness(self, project_id: str, vendor: str, source_mode: str = "live", source_version_id: str | None = None) -> dict[str, object]:
        project = project_service.ensure_project(project_id)
        paths = project_service.workspace_paths(project_id)

        source_mode_resolved, source_version_resolved = self._resolve_source_version(project_id, source_mode, source_version_id)

        checks: list[dict[str, object]] = []
        warnings: list[str] = []
        errors: list[str] = []

        def add_check(key: str, label: str, ready: bool, level: str, message: str) -> None:
            checks.append({"key": key, "label": label, "ready": ready, "level": level, "message": message})
            if level == "warning":
                warnings.append(message)
            if level == "error":
                errors.append(message)

        add_check("project", "Project", True, "success", f"Project '{project.name}' is available.")

        plant_graph_exists = (paths.plant_graph / "latest_graph.json").exists() or any(paths.plant_graph.rglob("*.json"))
        add_check(
            "plant_model",
            "Plant Model",
            plant_graph_exists,
            "success" if plant_graph_exists else "error",
            "Parsed plant model found." if plant_graph_exists else "Parsed plant model is missing.",
        )

        st_files: list[STSourceFile] = []
        logic_model: LogicModel | None = None
        st_ready = True
        try:
            st_files = self._load_st_files(project_id)
            logic_model = build_logic_model(project_id=str(project.id), project_name=project.name, owner=project.owner, st_files=st_files)
        except HTTPException:
            st_ready = False
        add_check(
            "st_logic",
            "ST Logic",
            st_ready,
            "success" if st_ready else "error",
            f"{len(st_files)} ST file(s) are available." if st_ready else "ST logic files are missing.",
        )

        loop_rows = control_loop_store.list_loops(project_id)
        loops_required = bool(logic_model and len(logic_model.loops) > 0)
        loops_ready = (len(loop_rows) > 0) if loops_required else True
        loops_level = "success" if loops_ready else "error"
        loops_message = (
            f"{len(loop_rows)} control loop(s) available."
            if loops_ready
            else "Control loops are required by generated logic but none are detected."
        )
        add_check("loops", "Control Loops", loops_ready, loops_level, loops_message)

        io_report_raw = logic_service.get_latest_io_mapping(project_id)
        io_report = self._safe_dict(io_report_raw)
        io_rows = self._safe_list(io_report.get("rows"))
        io_issues = self._safe_list(io_report.get("issues"))
        io_status = str(io_report.get("status") or "")
        io_ready = len(io_rows) > 0
        add_check(
            "io_mapping",
            "IO Mapping",
            io_ready,
            "success" if io_ready else "error",
            f"{len(io_rows)} IO mapping row(s) available." if io_ready else "IO mapping is missing.",
        )

        required_tags: set[str] = set()
        physical_candidates: set[str] = set()
        if logic_model is not None:
            required_tags.update(self._normalize_tag_name(tag.name) for tag in logic_model.tags)
            for io_meta in logic_model.io_metadata:
                io_meta_name = self._normalize_tag_name(str(io_meta.get("name") or ""))
                if io_meta_name:
                    physical_candidates.add(io_meta_name)

        for loop in loop_rows:
            sensor_tag = self._normalize_tag_name(getattr(loop, "sensor_tag", ""))
            actuator_tag = self._normalize_tag_name(getattr(loop, "actuator_tag", ""))
            setpoint_tag = self._normalize_tag_name(getattr(loop, "setpoint_tag", ""))
            output_tag = self._normalize_tag_name(getattr(loop, "output_tag", ""))

            required_tags.update(tag for tag in (sensor_tag, actuator_tag, setpoint_tag, output_tag) if tag)
            physical_candidates.update(tag for tag in (sensor_tag, actuator_tag, output_tag) if tag)

        for row in io_rows:
            tag_name = self._normalize_tag_name(str(row.get("tag") or ""))
            io_type = self._normalize_tag_name(str(row.get("io_type") or ""))
            if tag_name and io_type in {"AI", "AO", "DI", "DO"}:
                physical_candidates.add(tag_name)

        mapped_tags = {self._normalize_tag_name(str(row.get("tag") or "")) for row in io_rows}
        mapped_io_types_by_tag = {
            self._normalize_tag_name(str(row.get("tag") or "")): self._normalize_tag_name(str(row.get("io_type") or ""))
            for row in io_rows
            if self._normalize_tag_name(str(row.get("tag") or ""))
        }

        expected_sensor_tags = {
            self._normalize_tag_name(getattr(loop, "sensor_tag", ""))
            for loop in loop_rows
            if self._normalize_tag_name(getattr(loop, "sensor_tag", ""))
        }
        expected_actuator_tags = {
            self._normalize_tag_name(getattr(loop, "actuator_tag", ""))
            for loop in loop_rows
            if self._normalize_tag_name(getattr(loop, "actuator_tag", ""))
        }

        sensor_io_mismatches = sorted(
            tag for tag in expected_sensor_tags if tag in mapped_io_types_by_tag and mapped_io_types_by_tag[tag] not in {"AI", "DI"}
        )
        actuator_io_mismatches = sorted(
            tag for tag in expected_actuator_tags if tag in mapped_io_types_by_tag and mapped_io_types_by_tag[tag] not in {"AO", "DO"}
        )
        missing_required_tags = sorted(tag for tag in required_tags if tag and tag not in mapped_tags)

        blocking_physical_tags: set[str] = set()
        auto_resolved_derived_tags: set[str] = set()
        unresolved_derived_tags: set[str] = set()
        internal_control_tags: set[str] = set()
        unknown_tags: set[str] = set()
        unknown_hardware_like_tags: set[str] = set()

        for tag in missing_required_tags:
            parent_tag = self._resolve_parent_base_tag(tag)
            if parent_tag and parent_tag in mapped_tags:
                auto_resolved_derived_tags.add(tag)
                continue

            if self._is_internal_control_tag(tag):
                internal_control_tags.add(tag)
                continue

            if parent_tag:
                unresolved_derived_tags.add(tag)
                continue

            if self.is_physical_io_tag(tag, physical_candidates):
                blocking_physical_tags.add(tag)
                continue

            if self._looks_like_hardware_endpoint(tag):
                unknown_tags.add(tag)
                unknown_hardware_like_tags.add(tag)
                continue

            unknown_tags.add(tag)

        unmapped_physical_tags = sorted(blocking_physical_tags | unknown_hardware_like_tags)
        unmapped_logical_tags = sorted(unresolved_derived_tags | internal_control_tags | (unknown_tags - unknown_hardware_like_tags))
        required_physical_tags = sorted(tag for tag in required_tags if self.is_physical_io_tag(tag, physical_candidates))
        required_non_physical_tags = sorted(tag for tag in required_tags if tag not in set(required_physical_tags))

        blocking_io_issues = [
            issue
            for issue in io_issues
            if str(issue.get("severity")) == "error"
            and (
                not self._normalize_tag_name(str(issue.get("tag") or ""))
                or self.is_physical_io_tag(self._normalize_tag_name(str(issue.get("tag") or "")), physical_candidates)
            )
        ]
        warning_logical_issues = [
            issue
            for issue in io_issues
            if self._normalize_tag_name(str(issue.get("tag") or ""))
            and not self.is_physical_io_tag(self._normalize_tag_name(str(issue.get("tag") or "")), physical_candidates)
        ]

        has_blocking_mapping_errors = bool(blocking_io_issues) or bool(sensor_io_mismatches) or bool(actuator_io_mismatches)
        add_check(
            "mapping_errors_blocking",
            "Blocking IO Validation",
            not has_blocking_mapping_errors,
            "success" if not has_blocking_mapping_errors else "error",
            "No blocking IO mapping errors."
            if not has_blocking_mapping_errors
            else (
                "Blocking IO mapping errors detected for physical tags. "
                + (
                    f"Sensors must map to AI/DI ({', '.join(sensor_io_mismatches[:4])}{' ...' if len(sensor_io_mismatches) > 4 else ''}). "
                    if sensor_io_mismatches
                    else ""
                )
                + (
                    f"Actuators must map to AO/DO ({', '.join(actuator_io_mismatches[:4])}{' ...' if len(actuator_io_mismatches) > 4 else ''})."
                    if actuator_io_mismatches
                    else ""
                )
            ).strip(),
        )

        has_logical_mapping_warnings = bool(unmapped_logical_tags) or bool(warning_logical_issues)
        add_check(
            "mapping_warnings_non_physical",
            "Non-Physical Mapping Warnings",
            True,
            "warning" if has_logical_mapping_warnings else "success",
            (
                "Derived alarm/limit/internal control tags do not require direct hardware IO mapping if their parent field signal is already mapped. "
                + (
                    f"Unmapped logical/internal tags: {', '.join(unmapped_logical_tags[:8])}{' ...' if len(unmapped_logical_tags) > 8 else ''}"
                    if unmapped_logical_tags
                    else "No logical/internal mapping warnings."
                )
            ),
        )

        add_check(
            "derived_auto_resolved",
            "Auto-Resolved Derived Tags",
            True,
            "success" if not auto_resolved_derived_tags else "warning",
            (
                "No derived tags required parent resolution."
                if not auto_resolved_derived_tags
                else f"Resolved by parent mapping: {', '.join(sorted(auto_resolved_derived_tags)[:8])}{' ...' if len(auto_resolved_derived_tags) > 8 else ''}"
            ),
        )

        add_check(
            "internal_control_non_blocking",
            "Non-Blocking Internal Tags",
            True,
            "success" if not internal_control_tags else "warning",
            (
                "No internal control tags pending mapping."
                if not internal_control_tags
                else f"Internal/control tags (warning only): {', '.join(sorted(internal_control_tags)[:8])}{' ...' if len(internal_control_tags) > 8 else ''}"
            ),
        )

        add_check(
            "unknown_unclassified",
            "Unknown / Unclassified Tags",
            len(unknown_hardware_like_tags) == 0,
            "error" if unknown_hardware_like_tags else ("warning" if unknown_tags else "success"),
            (
                f"Unknown tags that look like hardware endpoints (blocking): {', '.join(sorted(unknown_hardware_like_tags)[:8])}{' ...' if len(unknown_hardware_like_tags) > 8 else ''}"
                if unknown_hardware_like_tags
                else (
                    f"Unknown tags (warning): {', '.join(sorted(unknown_tags)[:8])}{' ...' if len(unknown_tags) > 8 else ''}"
                    if unknown_tags
                    else "No unknown/unclassified tags."
                )
            ),
        )

        required_tags_ok = len(unmapped_physical_tags) == 0 or not io_ready
        add_check(
            "required_tags_physical",
            "Required Physical IO Tags",
            required_tags_ok,
            "success" if required_tags_ok else "error",
            "All required physical IO tags are traceable through IO mapping."
            if required_tags_ok
            else f"Missing mapped physical IO tags: {', '.join(unmapped_physical_tags[:8])}{' ...' if len(unmapped_physical_tags) > 8 else ''}",
        )

        self._logger.info(
            "export_readiness_io_validation total_tags=%s physical_tags_count=%s non_physical_tags_count=%s blocking_physical_tags=%s auto_resolved_derived=%s internal_non_blocking=%s unknown_tags=%s final_blocker_count=%s io_status=%s",
            len(required_tags),
            len(required_physical_tags),
            len(required_non_physical_tags),
            len(unmapped_physical_tags),
            len(auto_resolved_derived_tags),
            len(internal_control_tags),
            len(unknown_tags),
            len(unmapped_physical_tags) + len(sensor_io_mismatches) + len(actuator_io_mismatches),
            io_status,
        )
        self._logger.debug(
            "export_readiness_io_validation_detail required_physical=%s required_non_physical=%s blocking_physical=%s auto_resolved_derived=%s unresolved_derived=%s internal_non_blocking=%s unknown=%s unmapped_logical=%s",
            required_physical_tags,
            required_non_physical_tags,
            sorted(blocking_physical_tags),
            sorted(auto_resolved_derived_tags),
            sorted(unresolved_derived_tags),
            sorted(internal_control_tags),
            sorted(unknown_tags),
            unmapped_logical_tags,
        )

        vendor_supported = vendor.lower() == "generic_st" or get_vendor_exporter(vendor) is not None
        add_check(
            "target_vendor",
            "Export Target",
            vendor_supported,
            "success" if vendor_supported else "error",
            "Export target is supported." if vendor_supported else f"Unsupported export vendor: {vendor}",
        )

        checks_by_key = {str(item.get("key") or ""): item for item in checks}
        core_export_keys = {"project", "plant_model", "st_logic", "target_vendor"}
        export_blockers = [
            str(checks_by_key[key].get("message") or "")
            for key in core_export_keys
            if key in checks_by_key and not bool(checks_by_key[key].get("ready"))
        ]
        deploy_blockers = [str(item.get("message") or "") for item in checks if not bool(item.get("ready")) and str(item.get("level")) == "error"]

        export_allowed = len(export_blockers) == 0
        deploy_allowed = len(deploy_blockers) == 0
        self._logger.info(
            "export_readiness_state export_allowed=%s deploy_allowed=%s unresolved_physical=%s unresolved_internal=%s export_blockers=%s deploy_blockers=%s",
            export_allowed,
            deploy_allowed,
            len(unmapped_physical_tags),
            len(unmapped_logical_tags),
            len(export_blockers),
            len(deploy_blockers),
        )
        self._logger.debug(
            "export_readiness_reason export_allowed_reason=%s deploy_blocked_reason=%s",
            "Core export prerequisites satisfied." if export_allowed else "; ".join(export_blockers[:3]),
            "None" if deploy_allowed else "; ".join(deploy_blockers[:3]),
        )
        return {
            "project_id": project_id,
            "vendor": vendor,
            "source_mode": source_mode_resolved,
            "source_version_id": source_version_resolved,
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
            "export_allowed": export_allowed,
            "export_blocked": not export_allowed,
            "deploy_allowed": deploy_allowed,
            "deploy_blocked": not deploy_allowed,
            "unresolved_physical_io_tags": unmapped_physical_tags,
            "unresolved_internal_tags": unmapped_logical_tags,
            "auto_resolved_derived_tags": sorted(auto_resolved_derived_tags),
            "unknown_unclassified_tags": sorted(unknown_tags),
            "export_blockers": export_blockers,
            "deploy_blockers": deploy_blockers,
            "generated_at": datetime.now(timezone.utc),
        }

    def get_readiness(self, project_id: str, vendor: str, source_mode: str = "live", source_version_id: str | None = None) -> dict[str, object]:
        return self._build_readiness(project_id=project_id, vendor=vendor, source_mode=source_mode, source_version_id=source_version_id)

    def _export_generic_st(self, run_root: Path, logic_model: LogicModel) -> VendorExportResult:
        root = run_root / "Generic_ST"
        logic_root = root / "logic"
        logic_root.mkdir(parents=True, exist_ok=True)

        generated_files: list[str] = []
        block_count = 0
        all_blocks = [
            *logic_model.programs,
            *logic_model.function_blocks,
            *logic_model.equipment_routines,
            *logic_model.loops,
            *logic_model.interlocks,
            *logic_model.alarms,
        ]
        for block in all_blocks:
            filename = self._sanitize_filename(f"{block.name}.st")
            target = logic_root / filename
            target.write_text(block.content, encoding="utf-8")
            generated_files.append(str(target.relative_to(run_root)))
            block_count += 1

        tags_file = root / "tags.json"
        tags_file.write_text(
            json.dumps([{"name": tag.name, "type": tag.data_type, "metadata": tag.metadata} for tag in logic_model.tags], indent=2),
            encoding="utf-8",
        )
        generated_files.append(str(tags_file.relative_to(run_root)))

        artifact = run_root / "Generic_ST_Project.zip"
        with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(root.rglob("*")):
                if file.is_file():
                    archive.write(file, arcname=str(file.relative_to(run_root)))

        return VendorExportResult(
            artifact_name=artifact.name,
            artifact_path=artifact,
            generated_files=sorted(generated_files + [artifact.name]),
            logic_block_count=block_count,
            tag_count=len(logic_model.tags),
            notes=["Generic vendor-neutral ST bundle generated as fallback export target."],
        )

    def _write_traceability_files(
        self,
        run_root: Path,
        export_id: str,
        project_id: str,
        vendor: str,
        source_mode: str,
        source_version_id: str | None,
        logic_model: LogicModel,
        io_rows: list[dict[str, object]],
        loops: list[object],
        vendor_result: VendorExportResult,
        readiness: dict[str, object],
    ) -> dict[str, object]:
        referenced_tags = sorted({tag for block in [*logic_model.programs, *logic_model.function_blocks, *logic_model.loops, *logic_model.equipment_routines] for tag in self._extract_tag_tokens(block.content)})
        mapped_io_channels = [
            {
                "tag": row.get("tag"),
                "io_type": row.get("io_type"),
                "plc_id": row.get("plc_id"),
                "slot": row.get("slot"),
                "channel": row.get("channel"),
            }
            for row in io_rows
            if str(row.get("tag") or "") in referenced_tags
        ]

        blocks_traceability = []
        for block in [
            *logic_model.equipment_routines,
            *logic_model.loops,
            *logic_model.programs,
            *logic_model.function_blocks,
            *logic_model.interlocks,
            *logic_model.alarms,
        ]:
            tags_in_block = sorted(self._extract_tag_tokens(block.content))
            blocks_traceability.append(
                {
                    "block_name": block.name,
                    "block_kind": block.kind,
                    "source_file": block.source_file,
                    "referenced_tags": tags_in_block,
                    "referenced_io_channels": [item for item in mapped_io_channels if item.get("tag") in tags_in_block],
                }
            )

        loop_payload = [
            {
                "loop_tag": getattr(loop, "loop_tag", ""),
                "sensor_tag": getattr(loop, "sensor_tag", ""),
                "actuator_tag": getattr(loop, "actuator_tag", ""),
                "setpoint_tag": getattr(loop, "setpoint_tag", None),
                "output_tag": getattr(loop, "output_tag", None),
                "control_strategy": getattr(loop, "control_strategy", ""),
            }
            for loop in loops
        ]

        export_manifest = {
            "export_id": export_id,
            "project_id": project_id,
            "source_mode": source_mode,
            "source_version_id": source_version_id,
            "export_target": vendor,
            "export_timestamp": self._utcnow_iso(),
            "st_files": sorted([source.path for source in logic_model.source_files]),
            "referenced_tags": referenced_tags,
            "mapped_io_channels": mapped_io_channels,
            "loops_represented": [item["loop_tag"] for item in loop_payload if item["loop_tag"]],
            "vendor_artifact": vendor_result.artifact_name,
            "vendor_generated_files": vendor_result.generated_files,
            "unresolved_physical_io_tags": list(readiness.get("unresolved_physical_io_tags") or []),
            "unresolved_internal_tags": list(readiness.get("unresolved_internal_tags") or []),
            "export_generated_with_warnings": bool(readiness.get("unresolved_physical_io_tags") or readiness.get("unresolved_internal_tags")),
            "deploy_ready": bool(readiness.get("deploy_allowed", False)),
            "warning_summary": "Export generated for review/testing. Not deployment-ready until physical IO mappings are resolved.",
        }

        files = {
            "export_manifest.json": export_manifest,
            "tag_mapping.json": {
                "project_id": project_id,
                "tags": sorted([{"name": tag.name, "type": tag.data_type, "metadata": tag.metadata} for tag in logic_model.tags], key=lambda item: item["name"]),
            },
            "io_mapping_summary.json": {
                "project_id": project_id,
                "rows": io_rows,
                "total_rows": len(io_rows),
            },
            "control_loop_summary.json": {
                "project_id": project_id,
                "loop_count": len(loop_payload),
                "loops": loop_payload,
            },
            "st_block_traceability.json": {
                "project_id": project_id,
                "blocks": blocks_traceability,
            },
            "project_export_summary.json": {
                "project_id": project_id,
                "vendor": vendor,
                "logic_block_count": vendor_result.logic_block_count,
                "tag_count": vendor_result.tag_count,
                "generated_files": vendor_result.generated_files,
                "notes": vendor_result.notes,
            },
        }

        for file_name, payload in files.items():
            (run_root / file_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

        return export_manifest

    def _build_integration_package(
        self,
        run_root: Path,
        project_name: str,
        vendor: str,
        source_mode: str,
        source_version_id: str | None,
        vendor_result: VendorExportResult,
        logic_model: LogicModel,
    ) -> tuple[Path, list[str]]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        source_part = source_version_id or source_mode
        package_stem = f"{self._normalize_name(project_name)}_{vendor}_{self._sanitize_filename(source_part)}_{timestamp}".lower()
        package_name = f"{package_stem}.zip"
        package_path = run_root / package_name

        preview_files: list[str] = []
        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as archive:
            base = package_stem

            vendor_artifact_name = self._sanitize_filename(vendor_result.artifact_name)
            archive.write(vendor_result.artifact_path, arcname=f"{base}/vendor_artifact/{vendor_artifact_name}")
            preview_files.append(f"{base}/vendor_artifact/{vendor_artifact_name}")

            for file in sorted(run_root.glob("*.json")):
                archive.write(file, arcname=f"{base}/metadata/{file.name}")
                preview_files.append(f"{base}/metadata/{file.name}")

            for source in logic_model.source_files:
                archive.writestr(f"{base}/st_sources/{source.path}", source.content)
                preview_files.append(f"{base}/st_sources/{source.path}")

        return package_path, sorted(preview_files)

    def create_export(
        self,
        vendor: ExportVendor | str,
        project_id: str,
        source_mode: str = "live",
        source_version_id: str | None = None,
    ) -> dict[str, object]:
        project = project_service.get_project(project_id)
        readiness = self._build_readiness(project_id=project_id, vendor=str(vendor), source_mode=source_mode, source_version_id=source_version_id)
        if not bool(readiness.get("export_allowed")):
            raise HTTPException(status_code=409, detail={"message": "Export prerequisites failed.", "readiness": readiness})

        source_mode_resolved = str(readiness.get("source_mode") or "live")
        source_version_resolved = readiness.get("source_version_id")

        st_files = self._load_st_files(project_id)
        logic_model = build_logic_model(project_id=str(project.id), project_name=project.name, owner=project.owner, st_files=st_files)

        exporter = None if str(vendor).lower() == "generic_st" else get_vendor_exporter(str(vendor))
        if str(vendor).lower() != "generic_st" and exporter is None:
            raise HTTPException(status_code=400, detail=f"Unsupported export vendor: {vendor}")

        self._logger.info("export vendor_selected=%s project_id=%s source=%s", vendor, project_id, source_mode_resolved)

        export_id = str(uuid4())
        run_root = self._exports_root(project_id) / export_id
        run_root.mkdir(parents=True, exist_ok=True)

        if str(vendor).lower() == "generic_st":
            vendor_result = self._export_generic_st(run_root, logic_model)
        elif str(vendor).lower() == "siemens":
            vendor_root = self._exports_root(project_id) / project_id
            tia_dir = vendor_root / "TIA_Project"
            if tia_dir.exists():
                shutil.rmtree(tia_dir)
            vendor_root.mkdir(parents=True, exist_ok=True)
            vendor_result = exporter.export(vendor_root, logic_model)
        else:
            vendor_result = exporter.export(run_root, logic_model)

        io_report = self._safe_dict(logic_service.get_latest_io_mapping(project_id))
        io_rows = self._safe_list(io_report.get("rows"))
        loops = control_loop_store.list_loops(project_id)

        export_manifest = self._write_traceability_files(
            run_root=run_root,
            export_id=export_id,
            project_id=project_id,
            vendor=str(vendor),
            source_mode=source_mode_resolved,
            source_version_id=str(source_version_resolved) if source_version_resolved else None,
            logic_model=logic_model,
            io_rows=io_rows,
            loops=loops,
            vendor_result=vendor_result,
            readiness=readiness,
        )

        integration_package, package_preview = self._build_integration_package(
            run_root=run_root,
            project_name=project.name,
            vendor=str(vendor),
            source_mode=source_mode_resolved,
            source_version_id=str(source_version_resolved) if source_version_resolved else None,
            vendor_result=vendor_result,
            logic_model=logic_model,
        )

        manifest = {
            "export_id": export_id,
            "project_id": project_id,
            "project_name": project.name,
            "vendor": str(vendor),
            "source_mode": source_mode_resolved,
            "source_version_id": source_version_resolved,
            "generated_at": self._utcnow_iso(),
            "files": vendor_result.generated_files,
            "package_path": str(integration_package),
            "artifact_name": integration_package.name,
            "logic_block_count": vendor_result.logic_block_count,
            "tag_count": vendor_result.tag_count,
            "notes": vendor_result.notes,
            "readiness": readiness,
            "unresolved_physical_io_tags": list(readiness.get("unresolved_physical_io_tags") or []),
            "unresolved_internal_tags": list(readiness.get("unresolved_internal_tags") or []),
            "export_generated_with_warnings": bool(readiness.get("unresolved_physical_io_tags") or readiness.get("unresolved_internal_tags")),
            "deploy_ready": bool(readiness.get("deploy_allowed", False)),
            "warning_summary": "Export generated for review/testing. Not deployment-ready until physical IO mappings are resolved.",
            "package_preview": package_preview,
            "export_manifest": export_manifest,
            "vendor_artifact_path": str(vendor_result.artifact_path),
        }
        (run_root / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        self._logger.info(
            "export vendor=%s blocks=%s tags=%s package=%s",
            vendor,
            vendor_result.logic_block_count,
            vendor_result.tag_count,
            integration_package,
        )

        return {
            "export_id": export_id,
            "project_id": project_id,
            "project_name": project.name,
            "vendor": str(vendor),
            "source_mode": source_mode_resolved,
            "source_version_id": source_version_resolved,
            "generated_at": manifest["generated_at"],
            "files": vendor_result.generated_files,
            "download_url": f"/api/exports/{export_id}/download",
            "package_path": str(integration_package),
            "artifact_name": integration_package.name,
            "logic_block_count": vendor_result.logic_block_count,
            "tag_count": vendor_result.tag_count,
            "readiness": readiness,
            "package_preview": package_preview,
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

    def check_deployment_readiness(self, project_id: str, export_id: str, target_runtime: str, runtime_config: dict[str, object] | None = None) -> dict[str, object]:
        _, manifest = self._find_export_manifest(export_id)
        runtime_config = runtime_config or {}
        logs: list[str] = []
        errors: list[str] = []

        if str(manifest.get("project_id")) != project_id:
            errors.append("Export does not belong to selected project.")

        package_path = Path(str(manifest.get("package_path") or ""))
        if not package_path.exists():
            errors.append("Export package is missing.")
        else:
            logs.append(f"package_found:{package_path}")

        if not target_runtime.strip():
            logs.append("target_runtime_missing:validation_relaxed")

        if not runtime_config:
            logs.append("runtime_config_missing:validation_relaxed")

        readiness = manifest.get("readiness") if isinstance(manifest.get("readiness"), dict) else {}
        unresolved_physical_io_tags = [str(item) for item in (readiness.get("unresolved_physical_io_tags") or []) if str(item)]
        unresolved_internal_tags = [str(item) for item in (readiness.get("unresolved_internal_tags") or []) if str(item)]
        deploy_blockers = [str(item) for item in (readiness.get("deploy_blockers") or []) if str(item)]
        proceed_with_warnings = bool(unresolved_physical_io_tags or unresolved_internal_tags or deploy_blockers)

        if proceed_with_warnings:
            logs.append("readiness_warnings_present:true")
            logs.append(f"unresolved_physical_io_tags:{len(unresolved_physical_io_tags)}")
            logs.append(f"unresolved_internal_tags:{len(unresolved_internal_tags)}")
            if deploy_blockers:
                logs.append(f"deploy_blockers:{'; '.join(deploy_blockers[:3])}")

        state = "ready_to_deploy" if not errors else "not_ready"
        message = "Deployment handoff is ready." if not errors else "Deployment handoff is blocked by required payload checks."
        return {
            "project_id": project_id,
            "export_id": export_id,
            "target_runtime": target_runtime,
            "state": state,
            "message": message,
            "logs": logs,
            "errors": errors,
            "package_path": str(package_path) if package_path.exists() else None,
            "proceed_with_warnings": proceed_with_warnings,
            "readiness_state_at_action_time": {
                "export_allowed": bool(readiness.get("export_allowed", False)),
                "deploy_allowed": bool(readiness.get("deploy_allowed", False)),
                "deploy_blockers": deploy_blockers,
            },
            "unresolved_physical_io_tags": unresolved_physical_io_tags,
            "unresolved_internal_tags": unresolved_internal_tags,
        }

    def handoff_deployment(
        self,
        project_id: str,
        export_id: str,
        target_runtime: str,
        runtime_config: dict[str, object] | None = None,
        trigger_runtime_deploy: bool = False,
    ) -> dict[str, object]:
        run_root, _ = self._find_export_manifest(export_id)
        readiness = self.check_deployment_readiness(project_id, export_id, target_runtime, runtime_config)
        if readiness["state"] != "ready_to_deploy":
            return readiness

        package_path = Path(str(readiness.get("package_path") or ""))
        paths = project_service.workspace_paths(project_id)
        handoff_dir = paths.runtime / "export_handoff"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        handoff_package = handoff_dir / package_path.name
        shutil.copy2(package_path, handoff_package)

        logs = list(readiness.get("logs") or [])
        logs.append(f"handoff_package:{handoff_package}")

        handoff_summary = {
            "handoff_triggered_at": self._utcnow_iso(),
            "handoff_triggered_with_warnings": bool(readiness.get("proceed_with_warnings", False)),
            "deploy_triggered_with_warnings": bool(readiness.get("proceed_with_warnings", False)) if trigger_runtime_deploy else False,
            "unresolved_physical_io_tags": list(readiness.get("unresolved_physical_io_tags") or []),
            "unresolved_internal_tags": list(readiness.get("unresolved_internal_tags") or []),
            "readiness_state_at_action_time": readiness.get("readiness_state_at_action_time") or {},
        }
        (run_root / "handoff_summary.json").write_text(json.dumps(handoff_summary, indent=2), encoding="utf-8")
        logs.append(f"handoff_triggered_with_warnings:{str(handoff_summary['handoff_triggered_with_warnings']).lower()}")

        if not trigger_runtime_deploy:
            return {
                **readiness,
                "message": "Export package prepared for safe runtime handoff.",
                "logs": logs,
                "package_path": str(handoff_package),
                **handoff_summary,
            }

        try:
            logs.append("runtime_deploy:started")
            result = runtime_manager.deploy(project_id)
            status = str(result.get("status") or "failed")
            if status == "passed":
                logs.append("runtime_deploy:deployed")
                logs.append(f"deploy_triggered_with_warnings:{str(handoff_summary['deploy_triggered_with_warnings']).lower()}")
                deploy_summary = {
                    "deploy_triggered_at": self._utcnow_iso(),
                    **handoff_summary,
                }
                (run_root / "deploy_summary.json").write_text(json.dumps(deploy_summary, indent=2), encoding="utf-8")
                return {
                    **readiness,
                    "state": "deployed",
                    "message": "Runtime deployment completed from prepared export handoff.",
                    "logs": logs,
                    "errors": [],
                    "package_path": str(handoff_package),
                    **handoff_summary,
                }

            deploy_errors = [str(item) for item in (result.get("errors") or [])]
            logs.append("runtime_deploy:failed")
            return {
                **readiness,
                "state": "failed",
                "message": "Runtime deployment failed during handoff.",
                "logs": logs,
                "errors": deploy_errors or ["Runtime deployment returned failure."],
                "package_path": str(handoff_package),
                **handoff_summary,
            }
        except Exception as exc:
            logs.append("runtime_deploy:error")
            return {
                **readiness,
                "state": "failed",
                "message": "Runtime deployment failed during handoff.",
                "logs": logs,
                "errors": [str(exc)],
                "package_path": str(handoff_package),
                **handoff_summary,
            }

    def cleanup_export(self, export_id: str) -> None:
        run_root, _ = self._find_export_manifest(export_id)
        shutil.rmtree(run_root, ignore_errors=True)


export_engine = ExportEngine()
