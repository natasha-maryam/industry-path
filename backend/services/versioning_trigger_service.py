from __future__ import annotations

import logging
from typing import Any

from services.version_manager import version_manager


class VersioningTriggerService:
    """Shared helper for safe automatic versioning triggers across services."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def trigger_auto_commit(
        self,
        project_id: str,
        trigger_source: str,
        summary: str | None = None,
        *,
        deployment_success: bool = False,
    ) -> dict[str, Any] | None:
        try:
            commit_result = version_manager.auto_commit(
                project_id=project_id,
                trigger_source=trigger_source,
                summary=summary,
            )

            deployment_tag: str | None = None
            if deployment_success:
                tag_result = version_manager.create_deployment_tag(project_id, commit_result["version_tag"])
                deployment_tag = str(tag_result.get("deployment_tag") or "") or None

            self.logger.info(
                "Version trigger committed: trigger=%s project=%s version=%s commit=%s deployment_tag=%s",
                trigger_source,
                project_id,
                commit_result.get("version_tag"),
                commit_result.get("commit_hash"),
                deployment_tag,
            )
            return commit_result
        except Exception as exc:
            self.logger.warning(
                "Version trigger failed: trigger=%s project=%s error=%s",
                trigger_source,
                project_id,
                exc,
            )
            return None


versioning_trigger_service = VersioningTriggerService()
