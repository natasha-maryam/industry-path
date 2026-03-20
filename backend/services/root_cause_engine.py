from __future__ import annotations

import re
from typing import Any

from db.influx import influx_client
from db.neo4j import neo4j_client
from db.postgres import postgres_client


class RootCauseEngine:
    @staticmethod
    def _normalize_tag(tag: str) -> str:
        return re.sub(r"[^A-Z0-9]+", "", (tag or "").upper())

    @staticmethod
    def _alarm_to_sensor_candidates(alarm_tag: str) -> list[str]:
        value = (alarm_tag or "").strip().upper()
        if not value:
            return []

        # Common alarm/status suffixes for instrumentation tags.
        suffixes = [
            "_AHH",
            "_AH",
            "_AL",
            "_ALL",
            "_HH",
            "_H",
            "_L",
            "_LL",
            "_ALARM",
            "_FAULT",
            "_HI",
            "_LO",
        ]

        candidates = [value]
        for suffix in suffixes:
            if value.endswith(suffix):
                candidates.append(value[: -len(suffix)])
        return [item for item in candidates if item]

    def _resolve_project_id(self, alarm_tag: str, project_id: str | None) -> str | None:
        if project_id:
            return project_id
        row = postgres_client.fetch_one(
            """
            SELECT project_id::text AS project_id
            FROM control_loops
            WHERE sensor_tag = %s OR actuator_tag = %s OR loop_tag = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (alarm_tag, alarm_tag, alarm_tag),
        )
        return str(row.get("project_id")) if row else None

    def _load_project_control_loops(self, project_id: str) -> list[dict[str, Any]]:
        rows = postgres_client.fetch_all(
            """
            SELECT id::text AS id, project_id::text AS project_id, loop_tag, sensor_tag, actuator_tag,
                   process_unit, controller_tag, loop_type, control_strategy, setpoint_tag, output_tag,
                   status, confidence, created_at
            FROM control_loops
            WHERE project_id = %s
            ORDER BY confidence DESC, created_at DESC
            """,
            (project_id,),
        )
        return [dict(row) for row in rows]

    def _match_loop_by_sensor(self, alarm_tag: str, loops: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not loops:
            return None

        candidates = self._alarm_to_sensor_candidates(alarm_tag)
        normalized_candidates = {self._normalize_tag(item) for item in candidates}
        normalized_candidates.discard("")

        for loop in loops:
            sensor_tag = str(loop.get("sensor_tag") or "")
            normalized_sensor = self._normalize_tag(sensor_tag)
            if not normalized_sensor:
                continue
            if sensor_tag.upper() in candidates or normalized_sensor in normalized_candidates:
                return loop
        return None

    def _load_control_loop_reference(self, alarm_tag: str, project_id: str | None) -> dict[str, Any] | None:
        if project_id:
            project_loops = self._load_project_control_loops(project_id)
            matched = self._match_loop_by_sensor(alarm_tag, project_loops)
            if matched:
                return matched

        row = postgres_client.fetch_one(
            """
            SELECT id::text AS id, project_id::text AS project_id, loop_tag, sensor_tag, actuator_tag,
                   process_unit, controller_tag, loop_type, control_strategy, setpoint_tag, output_tag,
                   status, confidence, created_at
            FROM control_loops
            WHERE sensor_tag = %s OR actuator_tag = %s OR loop_tag = %s
            ORDER BY confidence DESC, created_at DESC
            LIMIT 1
            """,
            (alarm_tag, alarm_tag, alarm_tag),
        )
        return dict(row) if row else None

    def _neo4j_fault_path(self, project_id: str, alarm_tag: str, reference: dict[str, Any] | None) -> list[str]:
        if reference:
            path = [
                reference.get("sensor_tag") or "",
                reference.get("controller_tag") or "",
                reference.get("actuator_tag") or "",
                reference.get("process_unit") or "",
            ]
            return [node for node in path if node]

        nodes, edges = neo4j_client.fetch_project_graph(project_id)
        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            source = str(edge.get("source") or "")
            target = str(edge.get("target") or "")
            if not source or not target:
                continue
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set()).add(source)

        if alarm_tag not in adjacency:
            return [alarm_tag]

        best_neighbor = sorted(adjacency.get(alarm_tag, set()))[:1]
        path = [alarm_tag, *best_neighbor]
        if best_neighbor:
            next_neighbors = sorted(adjacency.get(best_neighbor[0], set()) - {alarm_tag})[:2]
            path.extend(next_neighbors)
        return path

    def analyze_alarm(self, alarm_tag: str, project_id: str | None = None) -> dict[str, Any]:
        reference = self._load_control_loop_reference(alarm_tag, project_id)
        resolved_project_id = self._resolve_project_id(alarm_tag, project_id)
        path = self._neo4j_fault_path(resolved_project_id, alarm_tag, reference) if resolved_project_id else [alarm_tag]
        timeline = influx_client.get_signal_history(path, points=10)

        if reference:
            loop_id = reference.get("loop_tag") or reference.get("id")
            actuator_tag = reference.get("actuator_tag")
            control_strategy = reference.get("control_strategy")
            root_cause = (
                f"Actuator {actuator_tag or 'UNKNOWN'} is the primary root cause candidate in loop {loop_id or 'UNKNOWN'} "
                f"using {control_strategy or 'UNKNOWN'} strategy."
            )
            confidence = round(min(0.99, max(0.78, float(reference.get("confidence") or 0.88))), 3)
        else:
            loop_id = None
            actuator_tag = None
            control_strategy = None
            root_cause = "Probable upstream process disturbance based on graph adjacency fallback analysis."
            confidence = round(min(0.55, max(0.32, 0.32 + 0.03 * max(0, len(path) - 1))), 3)

        affected_devices = sorted({item for item in path if item})

        return {
            "alarm": alarm_tag,
            "root_cause": root_cause,
            "path": path,
            "timeline": timeline,
            "confidence": confidence,
            "affected_devices": affected_devices,
            "loop_id": loop_id,
            "actuator_tag": actuator_tag,
            "control_strategy": control_strategy,
        }


root_cause_engine = RootCauseEngine()
