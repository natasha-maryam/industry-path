from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from db.postgres import postgres_client
from models.control_loop import ControlLoopRecord


class ControlLoopStore:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def upsert_project_loops(self, project_id: str, loops: list[ControlLoopRecord]) -> list[ControlLoopRecord]:
        created_at = datetime.now(timezone.utc)
        stored: list[ControlLoopRecord] = []
        loop_tags = [loop.loop_tag for loop in loops]

        if loop_tags:
            postgres_client.execute(
                "DELETE FROM control_loops WHERE project_id = %s AND NOT (loop_tag = ANY(%s))",
                (project_id, loop_tags),
            )
        else:
            postgres_client.execute("DELETE FROM control_loops WHERE project_id = %s", (project_id,))
            self.logger.info("Control loops upsert completed: project=%s upserted=0", project_id)
            return []

        for loop in loops:
            row_id = loop.id or str(uuid4())
            postgres_client.execute(
                """
                INSERT INTO control_loops (
                    id, project_id, loop_tag, sensor_tag, actuator_tag, process_unit, controller_tag,
                    loop_type, control_strategy, setpoint_tag, output_tag, status, confidence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, loop_tag)
                DO UPDATE SET
                    sensor_tag = EXCLUDED.sensor_tag,
                    actuator_tag = EXCLUDED.actuator_tag,
                    process_unit = EXCLUDED.process_unit,
                    controller_tag = EXCLUDED.controller_tag,
                    loop_type = EXCLUDED.loop_type,
                    control_strategy = EXCLUDED.control_strategy,
                    setpoint_tag = EXCLUDED.setpoint_tag,
                    output_tag = EXCLUDED.output_tag,
                    status = EXCLUDED.status,
                    confidence = EXCLUDED.confidence,
                    created_at = EXCLUDED.created_at
                """,
                (
                    row_id,
                    project_id,
                    loop.loop_tag,
                    loop.sensor_tag,
                    loop.actuator_tag,
                    loop.process_unit,
                    loop.controller_tag,
                    loop.loop_type,
                    loop.control_strategy,
                    loop.setpoint_tag,
                    loop.output_tag,
                    loop.status,
                    loop.confidence,
                    created_at,
                ),
            )

            stored.append(
                ControlLoopRecord(
                    id=row_id,
                    project_id=project_id,
                    loop_tag=loop.loop_tag,
                    sensor_tag=loop.sensor_tag,
                    actuator_tag=loop.actuator_tag,
                    process_unit=loop.process_unit,
                    controller_tag=loop.controller_tag,
                    loop_type=loop.loop_type,
                    control_strategy=loop.control_strategy,
                    setpoint_tag=loop.setpoint_tag,
                    output_tag=loop.output_tag,
                    status=loop.status,
                    confidence=float(loop.confidence),
                    created_at=created_at,
                )
            )

        self.logger.info("Control loops upsert completed: project=%s upserted=%s", project_id, len(stored))
        return stored

    def list_loops(self, project_id: str | None = None) -> list[ControlLoopRecord]:
        if project_id:
            rows = postgres_client.fetch_all(
                """
                SELECT id::text AS id, project_id::text AS project_id, loop_tag, sensor_tag, actuator_tag,
                       process_unit, controller_tag, loop_type, control_strategy, setpoint_tag, output_tag,
                       status, confidence, created_at
                FROM control_loops
                WHERE project_id = %s
                ORDER BY created_at DESC, loop_tag ASC
                """,
                (project_id,),
            )
        else:
            rows = postgres_client.fetch_all(
                """
                SELECT id::text AS id, project_id::text AS project_id, loop_tag, sensor_tag, actuator_tag,
                       process_unit, controller_tag, loop_type, control_strategy, setpoint_tag, output_tag,
                       status, confidence, created_at
                FROM control_loops
                ORDER BY created_at DESC, loop_tag ASC
                """
            )
        return [ControlLoopRecord.model_validate(dict(row)) for row in rows]

    def get_loop(self, loop_tag: str, project_id: str | None = None) -> ControlLoopRecord | None:
        if project_id:
            row = postgres_client.fetch_one(
                """
                SELECT id::text AS id, project_id::text AS project_id, loop_tag, sensor_tag, actuator_tag,
                       process_unit, controller_tag, loop_type, control_strategy, setpoint_tag, output_tag,
                       status, confidence, created_at
                FROM control_loops
                WHERE loop_tag = %s AND project_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (loop_tag, project_id),
            )
        else:
            row = postgres_client.fetch_one(
                """
                SELECT id::text AS id, project_id::text AS project_id, loop_tag, sensor_tag, actuator_tag,
                       process_unit, controller_tag, loop_type, control_strategy, setpoint_tag, output_tag,
                       status, confidence, created_at
                FROM control_loops
                WHERE loop_tag = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (loop_tag,),
            )

        if row is None:
            return None
        return ControlLoopRecord.model_validate(dict(row))


control_loop_store = ControlLoopStore()
