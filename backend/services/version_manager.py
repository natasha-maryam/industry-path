from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from models.logic import VersionSnapshotResult
from services.project_service import project_service


class VersionManager:
    """Snapshot generated logic artifacts and validation outputs for traceability."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def snapshot(self, project_id: str, artifact_paths: list[str]) -> VersionSnapshotResult:
        snapshot_id = str(uuid4())
        paths = project_service.workspace_paths(project_id)
        snapshot_file = paths.snapshots / f"{snapshot_id}.json"

        payload = {
            "project_id": project_id,
            "snapshot_id": snapshot_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifact_paths,
            "backend": "filesystem",
            # TODO: Integrate GitPython/Dolt metadata and commit hash once available.
            "todo": "VCS provider integration pending.",
        }
        snapshot_file.write_text(json.dumps(payload, indent=2))

        self.logger.info("Version snapshot created: project=%s snapshot_id=%s", project_id, snapshot_id)
        return VersionSnapshotResult(
            project_id=project_id,
            snapshot_id=snapshot_id,
            artifacts=artifact_paths,
            backend="filesystem",
        )


version_manager = VersionManager()
