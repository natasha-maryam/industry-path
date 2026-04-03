from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from db.postgres import postgres_client
from models.plant_genie import PlantGenieAIBindingRequest, PlantGenieAIBindingResponse
from services.plant_genie_plant_data_service import plant_genie_plant_data_connector_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PlantGenieAIBindingService:
    def get_binding(self, user_id: str) -> PlantGenieAIBindingResponse:
        row = postgres_client.fetch_one(
            """
            SELECT
              bindings.id::text AS id,
              bindings.user_id,
              bindings.data_source_connector_id::text AS data_source_connector_id,
              bindings.config_json,
              bindings.created_at,
              bindings.updated_at,
              connectors.name AS data_source_connector_name,
              connectors.enabled AS source_connector_enabled,
              connectors.healthy AS source_connector_healthy
            FROM plant_genie_ai_bindings AS bindings
            LEFT JOIN plant_genie_plant_data_connectors AS connectors
              ON connectors.id = bindings.data_source_connector_id
             AND connectors.user_id = bindings.user_id
            WHERE bindings.user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        if row is None:
            return PlantGenieAIBindingResponse()
        return self._row_to_response(row)

    def upsert_binding(self, user_id: str, payload: PlantGenieAIBindingRequest) -> PlantGenieAIBindingResponse:
        connector = plant_genie_plant_data_connector_service.get_connector_record(user_id, payload.data_source_connector_id)
        timestamp = _utc_now()
        binding_id = str(uuid4())
        config_json = json.dumps(
            {
                "tag_scope": payload.tag_scope,
                "selected_tags": payload.selected_tags,
                "context_mode": payload.context_mode,
                "sampling_mode": payload.sampling_mode,
                "sampling_interval_ms": payload.sampling_interval_ms,
                "ai_access_mode": payload.ai_access_mode,
                "include_system_structure": payload.include_system_structure,
                "ai_api_input": payload.ai_api_input,
            }
        )
        row = postgres_client.fetch_one(
            """
            INSERT INTO plant_genie_ai_bindings (
              id,
              user_id,
              data_source_connector_id,
              config_json,
              created_at,
              updated_at
            )
            VALUES (%s, %s, %s::uuid, %s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET
              data_source_connector_id = EXCLUDED.data_source_connector_id,
              config_json = EXCLUDED.config_json,
              updated_at = EXCLUDED.updated_at
            RETURNING
              id::text AS id,
              user_id,
              data_source_connector_id::text AS data_source_connector_id,
              config_json,
              created_at,
              updated_at
            """,
            (
                binding_id,
                user_id,
                connector.id,
                config_json,
                timestamp,
                timestamp,
            ),
        )
        if row is None:
            raise RuntimeError("Failed to save Plant Genie AI binding")
        hydrated = dict(row)
        hydrated["data_source_connector_name"] = connector.name
        hydrated["source_connector_enabled"] = connector.enabled
        hydrated["source_connector_healthy"] = connector.healthy
        return self._row_to_response(hydrated)

    def get_binding_config(self, user_id: str) -> dict[str, Any] | None:
        row = postgres_client.fetch_one(
            """
            SELECT data_source_connector_id::text AS data_source_connector_id, config_json
            FROM plant_genie_ai_bindings
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        if row is None:
            return None
        config = self._load_config(row.get("config_json"))
        config["data_source_connector_id"] = str(row.get("data_source_connector_id") or "").strip() or None
        return config

    @staticmethod
    def _load_config(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _row_to_response(self, row: dict[str, Any]) -> PlantGenieAIBindingResponse:
        config = self._load_config(row.get("config_json"))
        return PlantGenieAIBindingResponse(
            configured=True,
            data_source_connector_id=str(row.get("data_source_connector_id") or "").strip() or None,
            data_source_connector_name=str(row.get("data_source_connector_name") or "").strip() or None,
            tag_scope=str(config.get("tag_scope") or "all"),
            selected_tags=[str(tag).strip() for tag in config.get("selected_tags", []) if str(tag).strip()],
            context_mode=str(config.get("context_mode") or "live_only"),
            sampling_mode=str(config.get("sampling_mode") or "stream"),
            sampling_interval_ms=int(config["sampling_interval_ms"]) if config.get("sampling_interval_ms") is not None else None,
            ai_access_mode=str(config.get("ai_access_mode") or "read_only"),
            include_system_structure=bool(config.get("include_system_structure", False)),
            ai_api_input=str(config.get("ai_api_input") or "").strip() or None,
            source_connector_enabled=bool(row.get("source_connector_enabled", False)),
            source_connector_healthy=bool(row.get("source_connector_healthy", False)),
            updated_at=row.get("updated_at"),
        )


plant_genie_ai_binding_service = PlantGenieAIBindingService()