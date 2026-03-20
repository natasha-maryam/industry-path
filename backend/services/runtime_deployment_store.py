from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from psycopg2.extras import Json

from db.postgres import postgres_client
from models.runtime_deployment import RuntimeDeploymentRecord


class RuntimeDeploymentStore:
    def upsert_project_deployment(
        self,
        *,
        project_id: str,
        target_runtime: str,
        protocol: str,
        plc_address: str | None,
        io_config_json: list[dict],
        deploy_status: str,
        validation_status: str,
        deployed_version: str | None,
        artifact_path: str | None,
        last_error: str | None,
    ) -> RuntimeDeploymentRecord:
        current = self.get_latest(project_id)
        now = datetime.now(timezone.utc)
        started_at = current.started_at if current else now
        row_id = current.id if current else str(uuid4())

        postgres_client.execute(
            """
            INSERT INTO runtime_deployments (
                id,
                project_id,
                target_runtime,
                protocol,
                plc_address,
                io_config_json,
                deploy_status,
                validation_status,
                deployed_version,
                artifact_path,
                last_error,
                started_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id)
            DO UPDATE SET
                target_runtime = EXCLUDED.target_runtime,
                protocol = EXCLUDED.protocol,
                plc_address = EXCLUDED.plc_address,
                io_config_json = EXCLUDED.io_config_json,
                deploy_status = EXCLUDED.deploy_status,
                validation_status = EXCLUDED.validation_status,
                deployed_version = EXCLUDED.deployed_version,
                artifact_path = EXCLUDED.artifact_path,
                last_error = EXCLUDED.last_error,
                started_at = EXCLUDED.started_at,
                updated_at = EXCLUDED.updated_at
            """,
            (
                row_id,
                project_id,
                target_runtime,
                protocol,
                plc_address,
                Json(io_config_json),
                deploy_status,
                validation_status,
                deployed_version,
                artifact_path,
                last_error,
                started_at,
                now,
            ),
        )

        return RuntimeDeploymentRecord(
            id=row_id,
            project_id=project_id,
            target_runtime=target_runtime,
            protocol=protocol,
            plc_address=plc_address,
            io_config_json=io_config_json,
            deploy_status=deploy_status,
            validation_status=validation_status,
            deployed_version=deployed_version,
            artifact_path=artifact_path,
            last_error=last_error,
            started_at=started_at,
            updated_at=now,
        )

    def get_latest(self, project_id: str) -> RuntimeDeploymentRecord | None:
        row = postgres_client.fetch_one(
            """
            SELECT id::text AS id,
                   project_id::text AS project_id,
                   target_runtime,
                   protocol,
                   plc_address,
                   coalesce(io_config_json, '[]'::jsonb) AS io_config_json,
                   deploy_status,
                   validation_status,
                   deployed_version,
                   artifact_path,
                   last_error,
                   started_at,
                   updated_at
            FROM runtime_deployments
            WHERE project_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (project_id,),
        )
        if not row:
            return None
        return RuntimeDeploymentRecord.model_validate(dict(row))


runtime_deployment_store = RuntimeDeploymentStore()
