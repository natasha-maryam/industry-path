from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from collections import defaultdict
from psycopg2.extras import Json

from db.postgres import postgres_client
from models.io_mapping import IOMappingGenerateResponse, IOMappingIssue, IOMappingRow, IOMappingSummary
from models.logic import CompletedLogicModel, IOMappingChannel, IOMappingResult
from models.graph import PlantGraph
from services.project_service import project_service
from services.st_codegen_utils import st_codegen_utils


class IOMappingEngine:
    """Derive deterministic PLC IO channels from graph and completed logic model."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _humanize(token: str | None) -> str:
        if not token:
            return "Unknown"
        return token.replace("_", " ").strip().title()

    @staticmethod
    def _normalize_tag(tag: str | None) -> str:
        return st_codegen_utils.normalize_symbol(tag)

    @classmethod
    def _classify_from_metadata(cls, node_type: str | None, signal_type: str | None, control_role: str | None) -> str | None:
        signal = (signal_type or "").lower()
        node = (node_type or "").lower()
        role = (control_role or "").lower()

        if signal in {"analog", "level", "pressure", "flow", "temperature", "analyzer"}:
            return "AI"
        if signal in {"digital", "boolean", "bool", "switch"}:
            return "DI"

        if any(keyword in role for keyword in {"actuator", "valve", "pump", "blower", "command"}):
            return "DO"

        analog_nodes = {
            "flow_transmitter",
            "level_transmitter",
            "pressure_transmitter",
            "differential_pressure_transmitter",
            "temperature_transmitter",
            "analyzer",
        }
        digital_nodes = {"level_switch", "pressure_switch", "limit_switch"}
        analog_output_nodes = {"control_valve", "variable_speed_drive"}
        digital_output_nodes = {"pump", "blower", "valve", "chemical_system_device"}

        if node in analog_nodes:
            return "AI"
        if node in digital_nodes:
            return "DI"
        if node in analog_output_nodes:
            return "AO"
        if node in digital_output_nodes:
            return "DO"
        return None

    def _collect_signal_candidates(self, graph: PlantGraph, model: CompletedLogicModel) -> list[dict[str, str]]:
        """Collect deterministic signal candidates from graph + completed logic metadata."""

        candidates: list[dict[str, str]] = []

        for node in sorted(graph.nodes, key=lambda item: item.id):
            io_type = self._classify_from_metadata(node.node_type, node.signal_type, node.control_role)
            candidates.append(
                {
                    "tag": self._normalize_tag(node.id),
                    "device_type": self._humanize(node.equipment_type or node.node_type),
                    "signal_type": self._humanize(node.signal_type or node.instrument_role or node.node_type),
                    "io_type": io_type or "",
                    "description": (node.description or node.label or node.id).strip(),
                }
            )

        for loop in sorted(model.loops, key=lambda item: item.loop_tag):
            pv_tag = self._normalize_tag(loop.pv_tag or loop.sensor_tag)
            out_tag = self._normalize_tag(loop.output_tag_analog or loop.output_tag or "")

            if pv_tag:
                candidates.append(
                    {
                        "tag": pv_tag,
                        "device_type": "Process Sensor",
                        "signal_type": "Process Variable",
                        "io_type": "AI",
                        "description": f"Loop PV for {self._normalize_tag(loop.loop_tag)}",
                    }
                )

            if out_tag:
                candidates.append(
                    {
                        "tag": out_tag,
                        "device_type": "Control Output",
                        "signal_type": "Control Output",
                        "io_type": "AO" if (loop.output_signal_type or "").lower() == "analog" else "DO",
                        "description": f"Loop output for {self._normalize_tag(loop.loop_tag)}",
                    }
                )

        for routine in sorted(model.equipment_routines, key=lambda item: item.equipment_tag):
            for tag, io_type, signal_type in (
                (routine.command_tag, "DO", "Command"),
                (routine.status_tag, "DI", "Status"),
                (routine.fault_tag, "DI", "Fault"),
                (routine.output_tag, "AO", "Output"),
            ):
                normalized = self._normalize_tag(tag)
                if not normalized:
                    continue
                candidates.append(
                    {
                        "tag": normalized,
                        "device_type": self._humanize(routine.equipment_type or "Equipment"),
                        "signal_type": signal_type,
                        "io_type": io_type,
                        "description": f"{signal_type} for {self._normalize_tag(routine.equipment_tag)}",
                    }
                )

        return candidates

    @staticmethod
    def _validate_candidates(candidates: list[dict[str, str]]) -> list[IOMappingIssue]:
        issues: list[IOMappingIssue] = []
        valid_io = {"AI", "AO", "DI", "DO"}
        seen: defaultdict[str, int] = defaultdict(int)

        for item in candidates:
            tag = item.get("tag", "")
            io_type = (item.get("io_type", "") or "").upper()
            seen[tag] += 1

            if not tag:
                issues.append(
                    IOMappingIssue(
                        code="missing_signal",
                        severity="error",
                        message="Signal tag is missing.",
                        tag=None,
                    )
                )

            if io_type and io_type not in valid_io:
                issues.append(
                    IOMappingIssue(
                        code="invalid_io_type",
                        severity="error",
                        message=f"Invalid IO type `{io_type}`.",
                        tag=tag or None,
                    )
                )

        for tag, count in seen.items():
            if tag and count > 1:
                issues.append(
                    IOMappingIssue(
                        code="duplicate_tag",
                        severity="error",
                        message=f"Duplicate tag detected: {tag} ({count} occurrences).",
                        tag=tag,
                    )
                )

        return issues

    @staticmethod
    def _dedupe_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
        output: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in candidates:
            tag = item.get("tag", "")
            if not tag or tag in seen:
                continue
            seen.add(tag)
            output.append(item)
        return output

    @staticmethod
    def _assign_channels(rows: list[IOMappingRow]) -> tuple[list[IOMappingRow], list[IOMappingIssue]]:
        issues: list[IOMappingIssue] = []
        ordered = sorted(rows, key=lambda item: (item.io_type, item.tag))
        counters: defaultdict[str, int] = defaultdict(int)
        base_slot = {"DI": 1, "DO": 2, "AI": 3, "AO": 4}

        for row in ordered:
            io_type = row.io_type.upper()
            current_index = counters[io_type]
            row.slot = base_slot.get(io_type, 10) + (current_index // 16)
            row.channel = (current_index % 16) + 1
            counters[io_type] += 1

            if row.channel < 1 or row.channel > 16:
                issues.append(
                    IOMappingIssue(
                        code="channel_overflow",
                        severity="error",
                        message=f"Channel overflow for tag {row.tag}.",
                        tag=row.tag,
                    )
                )

        return ordered, issues

    @staticmethod
    def _to_model_rows(rows: list[dict]) -> list[IOMappingRow]:
        return [IOMappingRow.model_validate(row) for row in rows]

    @staticmethod
    def _to_model_issues(issues: list[dict]) -> list[IOMappingIssue]:
        return [IOMappingIssue.model_validate(issue) for issue in issues]

    @staticmethod
    def _status_from_issues(issues: list[IOMappingIssue]) -> str:
        warning_count = sum(1 for item in issues if item.severity == "warning")
        error_count = sum(1 for item in issues if item.severity == "error")
        if error_count > 0:
            return "failed"
        if warning_count > 0:
            return "passed_with_warnings"
        return "passed"

    def _build_report(
        self,
        project_id: str,
        rows: list[IOMappingRow],
        issues: list[IOMappingIssue],
        **kwargs,
    ) -> IOMappingGenerateResponse:
        warning_count = sum(1 for item in issues if item.severity == "warning")
        error_count = sum(1 for item in issues if item.severity == "error")
        status = kwargs.get("status") or self._status_from_issues(issues)
        generated_at = kwargs.get("generated_at") or datetime.now(timezone.utc)
        return IOMappingGenerateResponse(
            project_id=project_id,
            version_id=kwargs.get("version_id"),
            version_number=kwargs.get("version_number"),
            generated_at=generated_at,
            is_active=kwargs.get("is_active", True),
            status=status,
            summary=IOMappingSummary(total_signals=len(rows), warning_count=warning_count, error_count=error_count),
            rows=rows,
            issues=issues,
        )

    @staticmethod
    def _write_artifacts(version_number: int, report: IOMappingGenerateResponse, output_dir: Path) -> tuple[str, str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_file = output_dir / f"io_mapping_v{version_number}.json"
        latest_file = output_dir / "io_mapping_latest.json"
        csv_file = output_dir / f"io_mapping_v{version_number}.csv"

        json_payload = report.model_dump(mode="json")
        json_file.write_text(json.dumps(json_payload, indent=2))
        latest_file.write_text(json.dumps(json_payload, indent=2))

        with csv_file.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tag", "device_type", "signal_type", "io_type", "plc_id", "slot", "channel", "description"])
            for row in report.rows:
                writer.writerow([
                    row.tag,
                    row.device_type,
                    row.signal_type,
                    row.io_type,
                    row.plc_id,
                    row.slot,
                    row.channel,
                    row.description,
                ])

        return (str(json_file), str(latest_file), str(csv_file))

    def save_io_mapping(self, project_id: str, rows: list[IOMappingRow], issues: list[IOMappingIssue]) -> dict:
        next_version_row = postgres_client.fetch_one(
            """
            SELECT COALESCE(MAX(version_number), 0) AS max_version
            FROM io_mapping_versions
            WHERE project_id = %s
            """,
            (project_id,),
        )
        version_number = int((next_version_row or {}).get("max_version") or 0) + 1
        version_id = str(uuid4())
        now = datetime.now(timezone.utc)

        report = self._build_report(
            project_id,
            rows,
            issues,
            version_id=version_id,
            version_number=version_number,
            generated_at=now,
            is_active=True,
        )

        paths = project_service.workspace_paths(project_id)
        version_json_path, _, _ = self._write_artifacts(version_number, report, paths.io_mapping)

        postgres_client.execute(
            "UPDATE io_mapping_versions SET is_active = FALSE WHERE project_id = %s",
            (project_id,),
        )
        postgres_client.execute(
            """
            INSERT INTO io_mapping_versions (
                id, project_id, version_number, is_active, status, summary, artifact_path, created_by, generated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                version_id,
                project_id,
                version_number,
                True,
                report.status,
                Json(report.summary.model_dump()),
                version_json_path,
                "system",
                now,
            ),
        )

        for row in rows:
            postgres_client.execute(
                """
                INSERT INTO io_mappings (
                    id, project_id, version_id, tag, device_type, signal_type, io_type,
                    plc_id, slot, channel, description, equipment, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    version_id,
                    row.tag,
                    row.device_type,
                    row.signal_type,
                    row.io_type,
                    row.plc_id,
                    row.slot,
                    row.channel,
                    row.description,
                    None,
                    now,
                ),
            )

        for issue in issues:
            postgres_client.execute(
                """
                INSERT INTO io_mapping_issues (
                    id, project_id, version_id, code, severity, message, tag, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    version_id,
                    issue.code,
                    issue.severity,
                    issue.message,
                    issue.tag,
                    now,
                ),
            )

        self.logger.info(
            "IO mapping version saved: project=%s version=%s rows=%s",
            project_id,
            version_number,
            len(rows),
        )
        return report.model_dump(mode="json")

    def get_latest_io_mapping(self, project_id: str) -> dict | None:
        version = postgres_client.fetch_one(
            """
            SELECT id, version_number, is_active, status, summary, generated_at
            FROM io_mapping_versions
            WHERE project_id = %s
            ORDER BY is_active DESC, generated_at DESC
            LIMIT 1
            """,
            (project_id,),
        )
        if version is None:
            return None

        rows = postgres_client.fetch_all(
            """
            SELECT tag, device_type, signal_type, io_type, plc_id, slot, channel, description
            FROM io_mappings
            WHERE project_id = %s AND version_id = %s
            ORDER BY slot ASC, channel ASC, tag ASC
            """,
            (project_id, version["id"]),
        )
        issues = postgres_client.fetch_all(
            """
            SELECT code, severity, message, tag
            FROM io_mapping_issues
            WHERE project_id = %s AND version_id = %s
            ORDER BY created_at ASC
            """,
            (project_id, version["id"]),
        )

        model_rows = self._to_model_rows(rows)
        model_issues = self._to_model_issues(issues)
        summary = IOMappingSummary.model_validate(version.get("summary") or {})
        report = IOMappingGenerateResponse(
            project_id=project_id,
            version_id=str(version["id"]),
            version_number=int(version["version_number"]),
            generated_at=version.get("generated_at") or datetime.now(timezone.utc),
            is_active=bool(version.get("is_active")),
            status=version.get("status") or self._status_from_issues(model_issues),
            summary=summary,
            rows=model_rows,
            issues=model_issues,
        )
        return report.model_dump(mode="json")

    def set_active_io_mapping_version(self, project_id: str, version_id: str) -> dict | None:
        version = postgres_client.fetch_one(
            """
            SELECT id, version_number
            FROM io_mapping_versions
            WHERE project_id = %s AND id = %s
            """,
            (project_id, version_id),
        )
        if version is None:
            return None

        postgres_client.execute(
            "UPDATE io_mapping_versions SET is_active = FALSE WHERE project_id = %s",
            (project_id,),
        )
        postgres_client.execute(
            "UPDATE io_mapping_versions SET is_active = TRUE WHERE project_id = %s AND id = %s",
            (project_id, version_id),
        )

        latest = self.get_latest_io_mapping(project_id)
        if latest is None:
            return None

        paths = project_service.workspace_paths(project_id)
        report = IOMappingGenerateResponse.model_validate(latest)
        self._write_artifacts(int(version["version_number"]), report, paths.io_mapping)
        return latest

    def generate_mapping_report(self, project_id: str, graph: PlantGraph, model: CompletedLogicModel) -> dict:
        """Generate deterministic IO mapping report with validation results."""

        candidates = self._collect_signal_candidates(graph, model)
        issues = self._validate_candidates(candidates)

        deduped = self._dedupe_candidates(candidates)
        rows = [
            IOMappingRow(
                tag=item["tag"],
                device_type=item["device_type"],
                signal_type=item["signal_type"],
                io_type=(item["io_type"] or "").upper() or "DI",
                plc_id="PLC1",
                slot=0,
                channel=0,
                description=item.get("description", ""),
            )
            for item in deduped
            if item.get("tag")
        ]

        rows, channel_issues = self._assign_channels(rows)
        issues.extend(channel_issues)

        saved_report = self.save_io_mapping(project_id, rows, issues)
        report = IOMappingGenerateResponse.model_validate(saved_report)

        self.logger.info(
            "IO mapping report generated: project=%s rows=%s warnings=%s errors=%s",
            project_id,
            len(rows),
            report.summary.warning_count,
            report.summary.error_count,
        )
        return report.model_dump(mode="json")

    @staticmethod
    def _classify(node_type: str) -> str | None:
        mapping = {
            "flow_transmitter": "AI",
            "level_transmitter": "AI",
            "pressure_transmitter": "AI",
            "differential_pressure_transmitter": "AI",
            "analyzer": "AI",
            "level_switch": "DI",
            "pump": "DO",
            "blower": "DO",
            "control_valve": "AO",
            "valve": "DO",
            "chemical_system_device": "DO",
        }
        return mapping.get(node_type)

    def build(self, project_id: str, graph: PlantGraph, model: CompletedLogicModel) -> IOMappingResult:
        report = self.generate_mapping_report(project_id, graph, model)
        channels: list[IOMappingChannel] = [
            IOMappingChannel(
                signal_tag=row["tag"],
                normalized_signal_tag=st_codegen_utils.normalize_symbol(row["tag"]),
                io_type=row["io_type"],
                plc_slot=row["slot"],
                plc_channel=row["channel"],
                source="graph+logic",
            )
            for row in report.get("rows", [])
        ]

        result = IOMappingResult(project_id=project_id, channels=channels)
        self.logger.info("IO mapping generated: project=%s channels=%s", project_id, len(channels))
        return result


io_mapping_engine = IOMappingEngine()
