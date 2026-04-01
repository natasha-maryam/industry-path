from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from db.postgres import postgres_client
from models.plant_genie import (
    PlantGeniePlantDataConnectorCreateRequest,
    PlantGeniePlantDataConnectorResponse,
    PlantGeniePlantDataConnectorRuntimeState,
    PlantGeniePlantDataConnectorType,
    PlantGeniePlantDataConnectorUpdateRequest,
    _validate_plant_data_connector_config,
    _validate_plant_data_connector_secrets,
)
from services.plant_genie_secret_store import plant_genie_secret_store


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


_UNSET = object()


@dataclass(frozen=True)
class PlantGeniePlantDataConnectorRecord:
    id: str
    user_id: str
    name: str
    connector_type: PlantGeniePlantDataConnectorType
    poll_interval_ms: int
    config: dict[str, Any]
    secrets: dict[str, Any]
    enabled: bool
    running: bool
    healthy: bool
    last_update: datetime | None
    last_tested_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class PlantGeniePlantDataConnectorService:
    def list_connectors(self, user_id: str) -> list[PlantGeniePlantDataConnectorResponse]:
        rows = postgres_client.fetch_all(
            """
            SELECT
              id::text AS id,
              user_id,
              name,
              connector_type,
              poll_interval_ms,
              config_json,
              secrets_encrypted,
              enabled,
              running,
              healthy,
              last_update,
              last_tested_at,
              last_error,
              created_at,
              updated_at
            FROM plant_genie_plant_data_connectors
            WHERE user_id = %s
            ORDER BY enabled DESC, updated_at DESC, created_at DESC
            """,
            (user_id,),
        )
        return [self._row_to_response(row) for row in rows]

    def create_connector(
        self,
        user_id: str,
        payload: PlantGeniePlantDataConnectorCreateRequest,
    ) -> PlantGeniePlantDataConnectorResponse:
        connector_id = str(uuid4())
        timestamp = _utc_now()
        config_json = json.dumps(payload.config)
        secrets_encrypted = self._encrypt_secrets(payload.secrets)
        with postgres_client.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM plant_genie_plant_data_connectors WHERE user_id = %s AND enabled = TRUE LIMIT 1",
                    (user_id,),
                )
                has_enabled_connector = cursor.fetchone() is not None
                cursor.execute(
                    """
                    INSERT INTO plant_genie_plant_data_connectors (
                      id,
                      user_id,
                      name,
                      connector_type,
                      poll_interval_ms,
                      config_json,
                      secrets_encrypted,
                      enabled,
                      running,
                      healthy,
                      last_update,
                      last_tested_at,
                      last_error,
                      created_at,
                      updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, FALSE, NULL, NULL, NULL, %s, %s)
                    RETURNING
                      id::text AS id,
                      user_id,
                      name,
                      connector_type,
                      poll_interval_ms,
                      config_json,
                      secrets_encrypted,
                      enabled,
                      running,
                      healthy,
                      last_update,
                      last_tested_at,
                      last_error,
                      created_at,
                      updated_at
                    """,
                    (
                        connector_id,
                        user_id,
                        payload.name,
                        payload.connector_type,
                        payload.poll_interval_ms,
                        config_json,
                        secrets_encrypted,
                        not has_enabled_connector,
                        timestamp,
                        timestamp,
                    ),
                )
                row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to create Plant Genie plant data connector")
        return self._row_to_response(row)

    def update_connector(
        self,
        user_id: str,
        connector_id: str,
        payload: PlantGeniePlantDataConnectorUpdateRequest,
    ) -> PlantGeniePlantDataConnectorResponse:
        current = self.get_connector_record(user_id, connector_id)
        config = _validate_plant_data_connector_config(payload.connector_type, payload.config)
        secrets = current.secrets if not payload.secrets else _validate_plant_data_connector_secrets(payload.connector_type, payload.secrets)
        timestamp = _utc_now()
        row = postgres_client.fetch_one(
            """
            UPDATE plant_genie_plant_data_connectors
            SET
              name = %s,
              connector_type = %s,
              poll_interval_ms = %s,
              config_json = %s,
              secrets_encrypted = %s,
              updated_at = %s
            WHERE id = %s::uuid AND user_id = %s
            RETURNING
              id::text AS id,
              user_id,
              name,
              connector_type,
              poll_interval_ms,
              config_json,
              secrets_encrypted,
              enabled,
              running,
              healthy,
              last_update,
              last_tested_at,
              last_error,
              created_at,
              updated_at
            """,
            (
                payload.name,
                payload.connector_type,
                payload.poll_interval_ms,
                json.dumps(config),
                self._encrypt_secrets(secrets),
                timestamp,
                connector_id,
                user_id,
            ),
        )
        if row is None:
            raise KeyError(connector_id)
        return self._row_to_response(row)

    def delete_connector(self, user_id: str, connector_id: str) -> None:
        deleted = postgres_client.fetch_one(
            "DELETE FROM plant_genie_plant_data_connectors WHERE id = %s::uuid AND user_id = %s RETURNING id::text AS id",
            (connector_id, user_id),
        )
        if deleted is None:
            raise KeyError(connector_id)

    def set_enabled(self, user_id: str, connector_id: str, enabled: bool) -> PlantGeniePlantDataConnectorResponse:
        timestamp = _utc_now()
        row = postgres_client.fetch_one(
            """
            UPDATE plant_genie_plant_data_connectors
            SET enabled = %s, updated_at = %s
            WHERE id = %s::uuid AND user_id = %s
            RETURNING
              id::text AS id,
              user_id,
              name,
              connector_type,
              poll_interval_ms,
              config_json,
              secrets_encrypted,
              enabled,
              running,
              healthy,
              last_update,
              last_tested_at,
              last_error,
              created_at,
              updated_at
            """,
            (enabled, timestamp, connector_id, user_id),
        )
        if row is None:
            raise KeyError(connector_id)
        return self._row_to_response(row)

    def update_runtime_state(
        self,
        connector_id: str,
        *,
        running: bool | None = None,
        healthy: bool | None = None,
        last_update: datetime | None | object = _UNSET,
        last_error: str | None | object = _UNSET,
    ) -> None:
        assignments: list[str] = []
        params: list[Any] = []
        if running is not None:
            assignments.append("running = %s")
            params.append(running)
        if healthy is not None:
            assignments.append("healthy = %s")
            params.append(healthy)
        if last_update is not _UNSET:
            assignments.append("last_update = %s")
            params.append(last_update)
        if last_error is not _UNSET:
            assignments.append("last_error = %s")
            params.append(last_error)
        if not assignments:
            return
        assignments.append("updated_at = %s")
        params.append(_utc_now())
        params.append(connector_id)
        postgres_client.execute(
            f"UPDATE plant_genie_plant_data_connectors SET {', '.join(assignments)} WHERE id = %s::uuid",
            tuple(params),
        )

    def list_enabled_connector_records(self) -> list[PlantGeniePlantDataConnectorRecord]:
        rows = postgres_client.fetch_all(
            """
            SELECT
              id::text AS id,
              user_id,
              name,
              connector_type,
              poll_interval_ms,
              config_json,
              secrets_encrypted,
              enabled,
              running,
              healthy,
              last_update,
              last_tested_at,
              last_error,
              created_at,
              updated_at
            FROM plant_genie_plant_data_connectors
            WHERE enabled = TRUE
            ORDER BY updated_at DESC, created_at DESC
            """
        )
        return [self._row_to_record(row) for row in rows]

    def get_connector_record(self, user_id: str, connector_id: str) -> PlantGeniePlantDataConnectorRecord:
        row = postgres_client.fetch_one(
            """
            SELECT
              id::text AS id,
              user_id,
              name,
              connector_type,
              poll_interval_ms,
              config_json,
              secrets_encrypted,
              enabled,
              running,
              healthy,
              last_update,
              last_tested_at,
              last_error,
              created_at,
              updated_at
            FROM plant_genie_plant_data_connectors
            WHERE id = %s::uuid AND user_id = %s
            LIMIT 1
            """,
            (connector_id, user_id),
        )
        if row is None:
            raise KeyError(connector_id)
        return self._row_to_record(row)

    def mark_test_result(
        self,
        user_id: str,
        connector_id: str,
        *,
        healthy: bool,
        message: str,
    ) -> PlantGeniePlantDataConnectorResponse:
        timestamp = _utc_now()
        row = postgres_client.fetch_one(
            """
            UPDATE plant_genie_plant_data_connectors
            SET
              healthy = %s,
              last_tested_at = %s,
              last_error = %s,
              updated_at = %s
            WHERE id = %s::uuid AND user_id = %s
            RETURNING
              id::text AS id,
              user_id,
              name,
              connector_type,
              poll_interval_ms,
              config_json,
              secrets_encrypted,
              enabled,
              running,
              healthy,
              last_update,
              last_tested_at,
              last_error,
              created_at,
              updated_at
            """,
            (healthy, timestamp, None if healthy else message[:4000], timestamp, connector_id, user_id),
        )
        if row is None:
            raise KeyError(connector_id)
        return self._row_to_response(row)

    @staticmethod
    def _encrypt_secrets(secrets: Mapping[str, Any]) -> str | None:
        normalized = {str(key): value for key, value in secrets.items() if value is not None and str(value).strip()}
        if not normalized:
            return None
        return plant_genie_secret_store.encrypt(json.dumps(normalized))

    @staticmethod
    def _decrypt_secrets(value: str | None) -> dict[str, Any]:
        if not value:
            return {}
        raw = plant_genie_secret_store.decrypt(value)
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}

    def _row_to_record(self, row: Mapping[str, Any]) -> PlantGeniePlantDataConnectorRecord:
        config = json.loads(str(row.get("config_json") or "{}"))
        return PlantGeniePlantDataConnectorRecord(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            name=str(row["name"]),
            connector_type=str(row["connector_type"]),
            poll_interval_ms=int(row.get("poll_interval_ms") or 5000),
            config=config if isinstance(config, dict) else {},
            secrets=self._decrypt_secrets(row.get("secrets_encrypted")),
            enabled=bool(row.get("enabled", False)),
            running=bool(row.get("running", False)),
            healthy=bool(row.get("healthy", False)),
            last_update=row.get("last_update"),
            last_tested_at=row.get("last_tested_at"),
            last_error=row.get("last_error"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_response(self, row: Mapping[str, Any]) -> PlantGeniePlantDataConnectorResponse:
        record = self._row_to_record(row)
        return PlantGeniePlantDataConnectorResponse(
            id=record.id,
            name=record.name,
            connector_type=record.connector_type,
            poll_interval_ms=record.poll_interval_ms,
            config=record.config,
            has_secrets=bool(record.secrets),
            runtime=PlantGeniePlantDataConnectorRuntimeState(
                enabled=record.enabled,
                running=record.running,
                healthy=record.healthy,
                last_update=record.last_update,
                last_error=record.last_error,
            ),
            health={
                "id": record.id,
                "healthy": record.healthy,
                "lastUpdate": record.last_update,
            },
            last_tested_at=record.last_tested_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


plant_genie_plant_data_connector_service = PlantGeniePlantDataConnectorService()