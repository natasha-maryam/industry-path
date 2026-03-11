from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from models.logic import IOMappingResult, RuntimeValidationResult, STGenerationResult
from services.project_service import project_service


class RuntimeDeployer:
    """Runtime readiness hooks for OpenPLC payload validation."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

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
