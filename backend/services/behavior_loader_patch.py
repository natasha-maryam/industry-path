from __future__ import annotations

import logging
from threading import RLock
from typing import Any, Mapping

from models.engineering_table import EngineeringTableRequest
from services.deterministic_behavior_service import deterministic_behavior_service
from services.engineering_table_parser import engineering_table_parser
from services.graph_service import graph_service
from services.project_service import project_service


logger = logging.getLogger(__name__)


class BehaviorLoaderPatch:
    def __init__(self) -> None:
        self._lock = RLock()
        self._active_project_id: str | None = None

    @staticmethod
    def _to_runtime_patch(value: Any) -> dict[str, Any]:
        return {
            "current_value": None if value is None else str(value),
        }

    @staticmethod
    def _normalize_changed_signals(changed_signals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        updates: dict[str, dict[str, Any]] = {}
        for item in changed_signals:
            tag = str(item.get("tag") or "").strip()
            if not tag:
                continue
            patch: dict[str, Any] = {}
            if "current" in item:
                patch["current_value"] = None if item.get("current") is None else str(item.get("current"))
            if "state" in item:
                patch["state"] = None if item.get("state") is None else str(item.get("state"))
            if "setpoint" in item:
                patch["setpoint"] = None if item.get("setpoint") is None else str(item.get("setpoint"))
            if "mode" in item:
                patch["mode"] = None if item.get("mode") is None else str(item.get("mode"))
            if "unit" in item:
                patch["unit"] = None if item.get("unit") is None else str(item.get("unit"))
            if patch:
                updates[tag] = patch
        return updates

    def _is_active_project(self, project_id: str) -> bool:
        with self._lock:
            return self._active_project_id == project_id

    def load_from_project(
        self,
        project_id: str,
        *,
        file_ids: list[str] | None = None,
        include_inferred: bool = True,
        max_flow_depth: int = 4,
    ) -> dict[str, Any]:
        project_service.ensure_project(project_id)

        table_payload = EngineeringTableRequest(
            project_id=project_id,
            file_ids=file_ids or [],
            include_inferred=include_inferred,
            max_flow_depth=max_flow_depth,
        )
        table_response = engineering_table_parser.build(table_payload)
        graph = graph_service.get_graph(project_id)

        result = deterministic_behavior_service.load(
            rows=[row.model_dump() for row in table_response.rows],
            edges=[edge.model_dump() for edge in graph.edges],
            runtime_seed=None,
        )

        with self._lock:
            self._active_project_id = project_id

        logger.info(
            "behavior_load project_id=%s rows=%s edges=%s snapshot_id=%s",
            project_id,
            len(table_response.rows),
            len(graph.edges),
            result.get("snapshot_id"),
        )

        return {
            "project_id": project_id,
            "rows": len(table_response.rows),
            "edges": len(graph.edges),
            "snapshot_id": result.get("snapshot_id"),
            "recomputed": result.get("recomputed", 0),
            "sample_tags": deterministic_behavior_service.get_sample_tags(limit=8),
        }

    def push_runtime_updates(
        self,
        project_id: str,
        updates: Mapping[str, Mapping[str, Any]],
        *,
        radius: int | None = None,
    ) -> dict[str, Any]:
        if not updates:
            return {
                "project_id": project_id,
                "skipped": True,
                "reason": "empty_updates",
            }

        if not self._is_active_project(project_id):
            return {
                "project_id": project_id,
                "skipped": True,
                "reason": "inactive_project",
            }

        response = deterministic_behavior_service.update_runtime_values(dict(updates), radius=radius)
        return {
            "project_id": project_id,
            "skipped": False,
            "snapshot_id": response.get("snapshot_id"),
            "changed_tags": response.get("changed_tags", []),
            "impacted_tags": response.get("impacted_tags", []),
            "updated_rows": len(response.get("updated_rows", [])),
        }

    def push_runtime_values(self, project_id: str, values: Mapping[str, Any], *, radius: int | None = None) -> dict[str, Any]:
        updates = {str(tag): self._to_runtime_patch(value) for tag, value in values.items() if str(tag).strip()}
        return self.push_runtime_updates(project_id, updates, radius=radius)

    def push_changed_signals(
        self,
        project_id: str,
        changed_signals: list[dict[str, Any]],
        *,
        radius: int | None = None,
    ) -> dict[str, Any]:
        updates = self._normalize_changed_signals(changed_signals)
        return self.push_runtime_updates(project_id, updates, radius=radius)

    def push_trace_rows(self, project_id: str, trace: list[dict[str, Any]], *, radius: int | None = None) -> dict[str, Any]:
        latest_by_tag: dict[str, Any] = {}
        for row in trace:
            tag = str(row.get("tag") or "").strip()
            if not tag:
                continue
            latest_by_tag[tag] = row.get("value")
        return self.push_runtime_values(project_id, latest_by_tag, radius=radius)


behavior_loader_patch = BehaviorLoaderPatch()


def load_parser_output_into_behavior_layer(
    project_id: str,
    rows: list[Mapping[str, Any]] | None = None,
    edges: list[Mapping[str, Any]] | None = None,
    *,
    file_ids: list[str] | None = None,
    include_inferred: bool = True,
    max_flow_depth: int = 4,
) -> dict[str, Any]:
    """Bridge parser output into deterministic behavior layer.

    If rows are not supplied, engineering rows are rebuilt from the existing project parse context.
    """
    if rows is not None and edges is not None:
        result = deterministic_behavior_service.load(rows=rows, edges=edges, runtime_seed=None)
        payload = {
            "project_id": project_id,
            "rows": len(rows),
            "edges": len(edges),
            "snapshot_id": result.get("snapshot_id"),
            "recomputed": result.get("recomputed", 0),
            "sample_tags": deterministic_behavior_service.get_sample_tags(limit=8),
        }
        logger.info(
            "behavior_parser_bridge loaded project_id=%s rows_loaded=%s edges_loaded=%s sample_tags=%s",
            project_id,
            payload["rows"],
            payload["edges"],
            payload["sample_tags"],
        )
        return payload

    payload = behavior_loader_patch.load_from_project(
        project_id,
        file_ids=file_ids,
        include_inferred=include_inferred,
        max_flow_depth=max_flow_depth,
    )
    logger.info(
        "behavior_parser_bridge loaded_from_project project_id=%s rows_loaded=%s edges_loaded=%s sample_tags=%s",
        project_id,
        payload.get("rows"),
        payload.get("edges"),
        deterministic_behavior_service.get_sample_tags(limit=8),
    )
    return payload


def push_runtime_snapshot_into_behavior_layer(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Bridge runtime/simulation/live payloads into deterministic behavior updates."""
    project_id = str(payload.get("project_id") or "").strip()
    if not project_id:
        return {
            "skipped": True,
            "reason": "missing_project_id",
        }

    updates_raw = payload.get("updates")
    if isinstance(updates_raw, Mapping):
        updates = {str(tag): dict(patch) for tag, patch in updates_raw.items() if str(tag).strip() and isinstance(patch, Mapping)}
        return behavior_loader_patch.push_runtime_updates(project_id, updates)

    current_values = payload.get("current_values")
    if isinstance(current_values, Mapping):
        values = {str(tag): value for tag, value in current_values.items() if str(tag).strip()}
        return behavior_loader_patch.push_runtime_values(project_id, values)

    changed_signals = payload.get("changed_signals")
    if isinstance(changed_signals, list):
        return behavior_loader_patch.push_changed_signals(project_id, [item for item in changed_signals if isinstance(item, dict)])

    trace_rows = payload.get("trace_rows")
    if isinstance(trace_rows, list):
        return behavior_loader_patch.push_trace_rows(project_id, [item for item in trace_rows if isinstance(item, dict)])

    return {
        "project_id": project_id,
        "skipped": True,
        "reason": "no_supported_payload",
    }
