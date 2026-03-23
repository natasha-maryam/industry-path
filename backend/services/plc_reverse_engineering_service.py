from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from models.plc_reverse_engineering import (
    ExtractedDevice,
    ExtractedIOEntry,
    ExtractedLogicReference,
    ExtractedRoutine,
    ExtractedTag,
    ExtractedVariable,
    PLCPhase1ExtractionResponse,
    PLCSourceFormat,
    ReverseEngineeringFileResult,
)
from services.normalize_tags import normalize_canonical_tag
from services.project_service import project_service
from services.upload_service import upload_service


class PLCReverseEngineeringService:
    _TAG_PATTERN = re.compile(r"\b[A-Za-z]{1,6}[-_ ]?\d{1,5}[A-Za-z0-9]{0,4}\b")
    _ST_VAR_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^;]+);", re.MULTILINE)
    _ST_ROUTINE_PATTERN = re.compile(r"^\s*(PROGRAM|FUNCTION_BLOCK|FUNCTION)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
    _ST_CALL_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")

    def _resolve_project_id(self, project_id: str | None) -> str:
        if project_id:
            project_service.ensure_project(project_id)
            return project_id
        active = project_service.get_active_project()
        if active is None:
            raise HTTPException(status_code=404, detail="No active project selected")
        return str(active.id)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def _phase1_root(self, project_id: str) -> Path:
        paths = project_service.workspace_paths(project_id)
        root = paths.root / "reverse_engineering" / "phase1"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _safe_decode(content: bytes) -> tuple[str, bool]:
        try:
            return content.decode("utf-8"), False
        except UnicodeDecodeError:
            return content.decode("latin-1", errors="ignore"), True

    @staticmethod
    def _is_probably_binary(content: bytes) -> bool:
        if not content:
            return False
        sample = content[:2048]
        return b"\x00" in sample

    def _detect_format(self, file_name: str, text: str, content: bytes) -> PLCSourceFormat:
        lower = file_name.lower().strip()
        if lower.endswith(".acd"):
            return "rockwell_acd"
        if lower.endswith(".l5x"):
            return "rockwell_l5x"
        if lower.endswith(".ap16"):
            return "siemens_ap16"
        if lower.endswith(".tsproj"):
            return "beckhoff_tsproj"
        if lower.endswith(".project"):
            return "codesys_project"
        if lower.endswith(".st"):
            if "openplc" in lower or "openplc" in text.lower():
                return "openplc_st"
            return "iec_st"
        if lower.endswith(".csv"):
            return "csv_io_table"

        trimmed = text.lstrip().lower()
        if trimmed.startswith("<?xml") or trimmed.startswith("<"):
            if any(token in trimmed for token in ("rslogix5000content", "rockwell", "allen-bradley")):
                return "rockwell_l5x"
            if "ladder" in trimmed or "rung" in trimmed:
                return "ladder_xml"
            if any(token in trimmed for token in ("siemens", "tia", "simatic")):
                return "siemens_xml"
            if any(token in trimmed for token in ("codesys", "3s-software")):
                return "codesys_xml"
            return "siemens_xml"

        if lower.endswith((".xml", ".awl", ".scl")):
            if "ladder" in text.lower() or "rung" in text.lower():
                return "ladder_xml"
            return "siemens_xml"

        if self._is_probably_binary(content):
            return "unknown"

        if "program" in text.lower() and "end_program" in text.lower():
            return "loose_st_files"
        return "unknown"

    @staticmethod
    def _classify_signal_type(canonical_tag: str) -> str | None:
        prefix = canonical_tag.split("-", 1)[0].upper()
        signal_map = {
            "AI": "analog_input",
            "AO": "analog_output",
            "DI": "digital_input",
            "DO": "digital_output",
            "PV": "process_variable",
            "SP": "setpoint",
            "CV": "controller_output",
            "FT": "flow_transmitter",
            "PT": "pressure_transmitter",
            "LT": "level_transmitter",
            "TT": "temperature_transmitter",
            "FI": "flow_indicator",
            "PI": "pressure_indicator",
            "LI": "level_indicator",
        }
        return signal_map.get(prefix)

    @staticmethod
    def _classify_device_type(canonical_tag: str) -> str | None:
        prefix = canonical_tag.split("-", 1)[0].upper()
        device_map = {
            "P": "pump",
            "XV": "onoff_valve",
            "CV": "control_valve",
            "MTR": "motor",
            "V": "valve",
            "TK": "tank",
            "B": "blower",
            "PLC": "controller",
        }
        return device_map.get(prefix)

    def _extract_tags_from_text(self, text: str, source_hint: str) -> list[ExtractedTag]:
        seen: set[str] = set()
        tags: list[ExtractedTag] = []
        for match in self._TAG_PATTERN.findall(text):
            canonical = normalize_canonical_tag(match)
            if not canonical or canonical in seen:
                continue
            seen.add(canonical)
            tags.append(
                ExtractedTag(
                    raw_tag=match,
                    canonical_tag=canonical,
                    signal_type=self._classify_signal_type(canonical),
                    device_type=self._classify_device_type(canonical),
                    source_hint=source_hint,
                )
            )
        return tags

    def _extract_st_metadata(
        self,
        text: str,
    ) -> tuple[list[ExtractedRoutine], list[ExtractedVariable], list[ExtractedLogicReference], list[ExtractedTag]]:
        routines = [
            ExtractedRoutine(name=name, routine_type=routine_type.lower(), language="st")
            for routine_type, name in self._ST_ROUTINE_PATTERN.findall(text)
        ]

        variables: list[ExtractedVariable] = []
        for var_name, dtype in self._ST_VAR_PATTERN.findall(text):
            variables.append(ExtractedVariable(name=var_name, data_type=dtype.strip(), scope="var"))

        routine_names = {routine.name for routine in routines}
        refs: list[ExtractedLogicReference] = []
        for call in self._ST_CALL_PATTERN.findall(text):
            if call in routine_names:
                continue
            refs.append(ExtractedLogicReference(source="st_logic", target=call, reference_type="call"))

        tags = self._extract_tags_from_text(text, source_hint="st")
        return routines, variables, refs, tags

    def _extract_xml_metadata(
        self,
        text: str,
    ) -> tuple[list[ExtractedRoutine], list[ExtractedVariable], list[ExtractedDevice], list[ExtractedIOEntry], list[ExtractedTag], list[str]]:
        warnings: list[str] = []
        routines: list[ExtractedRoutine] = []
        variables: list[ExtractedVariable] = []
        devices: list[ExtractedDevice] = []
        io_entries: list[ExtractedIOEntry] = []
        tags: list[ExtractedTag] = []

        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            warnings.append("XML parse failed; falling back to regex extraction only.")
            return routines, variables, devices, io_entries, self._extract_tags_from_text(text, source_hint="xml-regex"), warnings

        seen_tags: set[str] = set()
        for element in root.iter():
            tag_name = element.tag.lower()
            attrs = {k.lower(): (v or "") for k, v in element.attrib.items()}

            if any(token in tag_name for token in ("routine", "program", "pou", "functionblock", "function_block", "function")):
                candidate_name = attrs.get("name") or attrs.get("id") or (element.text or "").strip()
                if candidate_name:
                    routines.append(ExtractedRoutine(name=candidate_name, routine_type=tag_name, language="xml"))

            if any(token in tag_name for token in ("var", "variable", "symbol", "tag")):
                candidate_name = attrs.get("name") or attrs.get("tag") or attrs.get("symbol")
                dtype = attrs.get("type") or attrs.get("datatype")
                if candidate_name:
                    variables.append(ExtractedVariable(name=candidate_name, data_type=dtype or None, scope="xml"))

            if any(token in tag_name for token in ("device", "module", "controller", "cpu", "plc")):
                candidate_name = attrs.get("name") or attrs.get("id")
                if candidate_name:
                    devices.append(
                        ExtractedDevice(
                            name=candidate_name,
                            device_type=attrs.get("type") or tag_name,
                            address=attrs.get("address") or attrs.get("slot"),
                        )
                    )

            address = attrs.get("address") or attrs.get("io") or attrs.get("channel")
            io_tag = attrs.get("tag") or attrs.get("name")
            if address or any(token in tag_name for token in ("io", "channel", "point")):
                io_entries.append(
                    ExtractedIOEntry(
                        tag=io_tag,
                        address=address,
                        io_type=attrs.get("type") or attrs.get("direction"),
                        description=attrs.get("description") or None,
                    )
                )

            for candidate in (attrs.get("tag"), attrs.get("name"), attrs.get("symbol")):
                if not candidate:
                    continue
                canonical = normalize_canonical_tag(candidate)
                if not canonical or canonical in seen_tags:
                    continue
                seen_tags.add(canonical)
                tags.append(
                    ExtractedTag(
                        raw_tag=candidate,
                        canonical_tag=canonical,
                        signal_type=self._classify_signal_type(canonical),
                        device_type=self._classify_device_type(canonical),
                        source_hint="xml-attribute",
                    )
                )

        extra_tags = self._extract_tags_from_text(text, source_hint="xml-text")
        for item in extra_tags:
            if item.canonical_tag not in seen_tags:
                seen_tags.add(item.canonical_tag)
                tags.append(item)

        return routines, variables, devices, io_entries, tags, warnings

    def _extract_csv_io(
        self,
        text: str,
    ) -> tuple[list[ExtractedIOEntry], list[ExtractedTag], list[str]]:
        warnings: list[str] = []
        io_entries: list[ExtractedIOEntry] = []
        tags: list[ExtractedTag] = []
        seen_tags: set[str] = set()

        reader = csv.DictReader(StringIO(text))
        headers = [header.lower() for header in (reader.fieldnames or [])]
        if not headers:
            warnings.append("CSV appears empty or missing headers")
            return io_entries, tags, warnings

        tag_keys = [key for key in ("tag", "name", "signal", "point") if key in headers]
        address_keys = [key for key in ("address", "io_address", "channel", "terminal") if key in headers]
        type_keys = [key for key in ("type", "io_type", "direction") if key in headers]
        desc_keys = [key for key in ("description", "desc", "comment") if key in headers]

        for row in reader:
            normalized_row = {str(k).lower(): (str(v).strip() if v is not None else "") for k, v in row.items()}
            tag_val = next((normalized_row.get(key, "") for key in tag_keys if normalized_row.get(key)), "")
            address_val = next((normalized_row.get(key, "") for key in address_keys if normalized_row.get(key)), "")
            type_val = next((normalized_row.get(key, "") for key in type_keys if normalized_row.get(key)), "")
            desc_val = next((normalized_row.get(key, "") for key in desc_keys if normalized_row.get(key)), "")

            if not any((tag_val, address_val, type_val, desc_val)):
                continue

            io_entries.append(
                ExtractedIOEntry(
                    tag=tag_val or None,
                    address=address_val or None,
                    io_type=type_val or None,
                    description=desc_val or None,
                )
            )

            if tag_val:
                canonical = normalize_canonical_tag(tag_val)
                if canonical and canonical not in seen_tags:
                    seen_tags.add(canonical)
                    tags.append(
                        ExtractedTag(
                            raw_tag=tag_val,
                            canonical_tag=canonical,
                            signal_type=self._classify_signal_type(canonical),
                            device_type=self._classify_device_type(canonical),
                            source_hint="csv",
                        )
                    )

        return io_entries, tags, warnings

    def _extract_single_file(
        self,
        file_path: Path,
        original_name: str,
        stored_name: str,
        document_type: str,
    ) -> ReverseEngineeringFileResult:
        content = file_path.read_bytes()
        text, lossy_decode = self._safe_decode(content)
        detected_format = self._detect_format(original_name, text, content)

        warnings: list[str] = []
        errors: list[str] = []
        status = "ok"

        if lossy_decode:
            warnings.append("File required non-UTF8 decode fallback; extraction may be partial.")

        tags: list[ExtractedTag] = []
        variables: list[ExtractedVariable] = []
        routines: list[ExtractedRoutine] = []
        devices: list[ExtractedDevice] = []
        io_entries: list[ExtractedIOEntry] = []
        logic_references: list[ExtractedLogicReference] = []

        if detected_format in {"rockwell_acd", "siemens_ap16"}:
            status = "unsupported"
            errors.append(
                "Binary PLC project format detected. Phase 1 supports metadata extraction from exports (L5X/XML/ST/CSV)."
            )
            warnings.append("Export project to L5X/XML/ST for deeper reverse engineering.")
        elif detected_format in {"rockwell_l5x", "siemens_xml", "codesys_xml", "codesys_project", "beckhoff_tsproj", "ladder_xml"}:
            routines, variables, devices, io_entries, tags, xml_warnings = self._extract_xml_metadata(text)
            warnings.extend(xml_warnings)
            logic_references = [ExtractedLogicReference(source=item.name, target="xml_logic", reference_type="routine") for item in routines]
        elif detected_format in {"openplc_st", "iec_st", "loose_st_files"}:
            routines, variables, logic_references, tags = self._extract_st_metadata(text)
        elif detected_format == "csv_io_table":
            io_entries, tags, csv_warnings = self._extract_csv_io(text)
            warnings.extend(csv_warnings)
        else:
            status = "partial"
            warnings.append("Unknown source format; performed generic tag scan only.")
            tags = self._extract_tags_from_text(text, source_hint="generic")

        if status == "ok" and not any((tags, variables, routines, devices, io_entries, logic_references)):
            status = "partial"
            warnings.append("No structured metadata extracted from file.")

        if errors and status != "unsupported":
            status = "error"

        return ReverseEngineeringFileResult(
            original_name=original_name,
            stored_name=stored_name,
            document_type=document_type,
            detected_format=detected_format,
            status=status,
            tags=tags,
            variables=variables,
            routines=routines,
            devices=devices,
            io_entries=io_entries,
            logic_references=logic_references,
            warnings=warnings,
            errors=errors,
        )

    @staticmethod
    def _relative_to_project(project_id: str, absolute: Path) -> str:
        marker = Path("storage") / "projects" / project_id
        parts = absolute.parts
        try:
            idx = parts.index("storage")
            return str(Path(*parts[idx:]))
        except ValueError:
            return str(absolute)

    def _persist_run_artifacts(
        self,
        project_id: str,
        run_id: str,
        files: list[ReverseEngineeringFileResult],
        extracted_root: Path,
    ) -> None:
        run_root = extracted_root / "runs" / run_id
        files_root = run_root / "files"
        files_root.mkdir(parents=True, exist_ok=True)

        for item in files:
            output_file = files_root / f"{item.stored_name}.json"
            output_file.write_text(item.model_dump_json(indent=2), encoding="utf-8")
            item.extracted_output_path = self._relative_to_project(project_id, output_file)

        summary_file = run_root / "summary.json"
        summary_file.write_text(
            json.dumps(
                {
                    "project_id": project_id,
                    "run_id": run_id,
                    "generated_at": self._utcnow().isoformat(),
                    "status_counts": dict(Counter(item.status for item in files)),
                    "file_count": len(files),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        latest_pointer = extracted_root / "latest_run.json"
        latest_pointer.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "summary": self._relative_to_project(project_id, summary_file),
                    "generated_at": self._utcnow().isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    async def run_phase1(
        self,
        files: list[UploadFile],
        document_types: list[str] | None = None,
        project_id: str | None = None,
    ) -> PLCPhase1ExtractionResponse:
        resolved_project_id = self._resolve_project_id(project_id)
        upload_result = await upload_service.save_files(resolved_project_id, files, document_types)
        paths = project_service.workspace_paths(resolved_project_id)
        extracted_root = self._phase1_root(resolved_project_id)
        run_id = str(uuid4())

        file_results: list[ReverseEngineeringFileResult] = []
        for uploaded in upload_result.files:
            absolute_file = paths.documents / uploaded.stored_name
            result = self._extract_single_file(
                file_path=absolute_file,
                original_name=uploaded.original_name,
                stored_name=uploaded.stored_name,
                document_type=uploaded.document_type,
            )
            file_results.append(result)

        self._persist_run_artifacts(
            project_id=resolved_project_id,
            run_id=run_id,
            files=file_results,
            extracted_root=extracted_root,
        )

        all_warnings = [warning for item in file_results for warning in item.warnings]
        all_errors = [error for item in file_results for error in item.errors]

        final_status = "ok"
        if any(item.status == "error" for item in file_results):
            final_status = "error"
        elif any(item.status == "unsupported" for item in file_results):
            final_status = "partial"
        elif any(item.status == "partial" for item in file_results):
            final_status = "partial"

        return PLCPhase1ExtractionResponse(
            project_id=resolved_project_id,
            run_id=run_id,
            generated_at=self._utcnow(),
            status=final_status,
            extracted_root=self._relative_to_project(resolved_project_id, extracted_root),
            files=file_results,
            warnings=all_warnings,
            errors=all_errors,
        )


plc_reverse_engineering_service = PLCReverseEngineeringService()
