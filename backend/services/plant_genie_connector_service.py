from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from uuid import uuid4

from psycopg2.extras import RealDictCursor

from db.postgres import postgres_client
from models.plant_genie import (
    PlantGenieAIConnectorCreateRequest,
    PlantGenieAIConnectorResponse,
    PlantGenieAIConnectorUpdateRequest,
    PlantGenieAIProvider,
)
from services.plant_genie_config import (
    build_plant_genie_provider_endpoint,
    resolve_default_plant_genie_ai_provider,
    resolve_plant_genie_ai_provider_config,
)
from services.plant_genie_ai_binding_service import plant_genie_ai_binding_service
from services.plant_genie_plant_data_runtime import plant_genie_plant_data_runtime
from services.plant_genie_secret_store import plant_genie_secret_store


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


class PlantGenieConnectorNotConfiguredError(ValueError):
    pass


class PlantGenieConnectorInvocationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlantGenieActiveConnector:
    id: str
    name: str
    provider: PlantGenieAIProvider
    api_key: str
    model: str | None = None
    provider_label: str | None = None


class PlantGenieProviderAdapter:
    adapter_name = "generic-passthrough"

    def build_payload(self, connector: PlantGenieActiveConnector, prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "input": prompt,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Plant Genie, responding through a user-managed external AI connector.",
                },
                {
                    "role": "user",
                    "content": self._build_user_content(prompt, context),
                },
            ],
        }

    @staticmethod
    def _build_user_content(prompt: str, context: Mapping[str, Any]) -> str:
        live_context = context.get("live_plant_data")
        if not isinstance(live_context, Mapping):
            return prompt

        serialized_context = json.dumps(live_context, default=str, indent=2, sort_keys=True)
        return f"{prompt}\n\nLive plant context:\n{serialized_context}"


class OpenAICompatibleChatCompletionsAdapter(PlantGenieProviderAdapter):
    adapter_name = "openai-chat-completions"

    def build_payload(self, connector: PlantGenieActiveConnector, prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        model = _normalize_optional_text(connector.model)
        if not model:
            raise PlantGenieConnectorInvocationError(
                "This connector is missing a model. Open Settings > AI Connectors, add one, and try again."
            )

        return {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Plant Genie, responding through a user-managed external AI connector.",
                },
                {
                    "role": "user",
                    "content": self._build_user_content(prompt, context),
                },
            ],
        }


class AnthropicMessagesAdapter(PlantGenieProviderAdapter):
    adapter_name = "anthropic-messages"

    def build_payload(self, connector: PlantGenieActiveConnector, prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        model = _normalize_optional_text(connector.model)
        if not model:
            raise PlantGenieConnectorInvocationError(
                "This Anthropic connector is missing a model. Open Settings > AI Connectors, add one, and try again."
            )

        return {
            "model": model,
            "max_tokens": 1024,
            "system": "You are Plant Genie, responding through a user-managed external AI connector.",
            "messages": [
                {
                    "role": "user",
                    "content": self._build_user_content(prompt, context),
                }
            ],
        }


class PlantGenieConnectorService:
    def list_connectors(self, user_id: str) -> list[PlantGenieAIConnectorResponse]:
        rows = postgres_client.fetch_all(
            """
            SELECT
              id::text AS id,
              name,
                            provider,
                            model,
              provider_label,
              notes,
              is_active,
              health_status,
              health_message,
              last_tested_at,
              created_at,
              updated_at
            FROM plant_genie_ai_connectors
            WHERE user_id = %s
            ORDER BY is_active DESC, updated_at DESC, created_at DESC
            """,
            (user_id,),
        )
        return [self._row_to_response(row) for row in rows]

    def create_connector(self, user_id: str, payload: PlantGenieAIConnectorCreateRequest) -> PlantGenieAIConnectorResponse:
        connector_id = str(uuid4())
        timestamp = _utc_now()
        encrypted_api_key = plant_genie_secret_store.encrypt(payload.api_key)
        provider = resolve_default_plant_genie_ai_provider()

        with postgres_client.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id::text AS id FROM plant_genie_ai_connectors WHERE user_id = %s AND is_active = TRUE LIMIT 1",
                    (user_id,),
                )
                existing_active = cursor.fetchone()
                is_active = existing_active is None
                cursor.execute(
                    """
                    INSERT INTO plant_genie_ai_connectors (
                      id,
                      user_id,
                      name,
                                            provider,
                                            api_key_encrypted,
                                            model,
                      provider_label,
                      notes,
                      is_active,
                      health_status,
                      health_message,
                      last_tested_at,
                      created_at,
                      updated_at
                    )
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'unknown', NULL, NULL, %s, %s)
                    RETURNING
                      id::text AS id,
                      name,
                                            provider,
                                            model,
                      provider_label,
                      notes,
                      is_active,
                      health_status,
                      health_message,
                      last_tested_at,
                      created_at,
                      updated_at
                    """,
                    (
                        connector_id,
                        user_id,
                        payload.name,
                        provider,
                        encrypted_api_key,
                        _normalize_optional_text(payload.model),
                        payload.provider_label,
                        payload.notes,
                        is_active,
                        timestamp,
                        timestamp,
                    ),
                )
                row = cursor.fetchone()

        return self._row_to_response(row)

    def update_connector(
        self,
        user_id: str,
        connector_id: str,
        payload: PlantGenieAIConnectorUpdateRequest,
    ) -> PlantGenieAIConnectorResponse:
        current = self._get_connector_row(user_id, connector_id, include_secret=True)
        encrypted_api_key = current["api_key_encrypted"]
        if payload.api_key:
            encrypted_api_key = plant_genie_secret_store.encrypt(payload.api_key)

        timestamp = _utc_now()
        row = postgres_client.fetch_one(
            """
            UPDATE plant_genie_ai_connectors
            SET
              name = %s,
              api_key_encrypted = %s,
              provider_label = %s,
              notes = %s,
                            model = %s,
              updated_at = %s
            WHERE id = %s::uuid AND user_id = %s
            RETURNING
              id::text AS id,
              name,
                            provider,
                            model,
              provider_label,
              notes,
              is_active,
              health_status,
              health_message,
              last_tested_at,
              created_at,
              updated_at
            """,
            (
                payload.name,
                encrypted_api_key,
                payload.provider_label,
                payload.notes,
                _normalize_optional_text(payload.model),
                timestamp,
                connector_id,
                user_id,
            ),
        )
        if row is None:
            raise KeyError(connector_id)
        return self._row_to_response(row)

    def delete_connector(self, user_id: str, connector_id: str) -> None:
        current = self._get_connector_row(user_id, connector_id, include_secret=False)

        with postgres_client.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "DELETE FROM plant_genie_ai_connectors WHERE id = %s::uuid AND user_id = %s",
                    (connector_id, user_id),
                )
                if current.get("is_active"):
                    cursor.execute(
                        """
                        SELECT id::text AS id
                        FROM plant_genie_ai_connectors
                        WHERE user_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT 1
                        """,
                        (user_id,),
                    )
                    replacement = cursor.fetchone()
                    if replacement is not None:
                        cursor.execute(
                            "UPDATE plant_genie_ai_connectors SET is_active = TRUE, updated_at = %s WHERE id = %s::uuid",
                            (_utc_now(), replacement["id"]),
                        )

    def activate_connector(self, user_id: str, connector_id: str) -> PlantGenieAIConnectorResponse:
        _ = self._get_connector_row(user_id, connector_id, include_secret=False)
        timestamp = _utc_now()

        with postgres_client.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "UPDATE plant_genie_ai_connectors SET is_active = FALSE, updated_at = %s WHERE user_id = %s",
                    (timestamp, user_id),
                )
                cursor.execute(
                    """
                    UPDATE plant_genie_ai_connectors
                    SET is_active = TRUE, updated_at = %s
                    WHERE id = %s::uuid AND user_id = %s
                    RETURNING
                      id::text AS id,
                      name,
                                            provider,
                                            model,
                      provider_label,
                      notes,
                      is_active,
                      health_status,
                      health_message,
                      last_tested_at,
                      created_at,
                      updated_at
                    """,
                    (timestamp, connector_id, user_id),
                )
                row = cursor.fetchone()

        if row is None:
            raise KeyError(connector_id)
        return self._row_to_response(row)

    def test_connector(self, user_id: str, connector_id: str) -> tuple[PlantGenieAIConnectorResponse, str]:
        current = self._get_connector_row(user_id, connector_id, include_secret=True)
        connector = self._row_to_active_connector(current)
        healthy, message = self._probe_connector(connector)
        status = "healthy" if healthy else "unhealthy"
        timestamp = _utc_now()

        row = postgres_client.fetch_one(
            """
            UPDATE plant_genie_ai_connectors
            SET
              health_status = %s,
              health_message = %s,
              last_tested_at = %s,
              updated_at = %s
            WHERE id = %s::uuid AND user_id = %s
            RETURNING
              id::text AS id,
              name,
                            provider,
                            model,
              provider_label,
              notes,
              is_active,
              health_status,
              health_message,
              last_tested_at,
              created_at,
              updated_at
            """,
            (status, message, timestamp, timestamp, connector_id, user_id),
        )
        if row is None:
            raise KeyError(connector_id)
        return self._row_to_response(row), message

    def get_active_connector_name(self, user_id: str) -> str | None:
        row = postgres_client.fetch_one(
            "SELECT name FROM plant_genie_ai_connectors WHERE user_id = %s AND is_active = TRUE LIMIT 1",
            (user_id,),
        )
        if row is None:
            return None
        return str(row["name"])

    def get_active_connector(self, user_id: str) -> PlantGenieActiveConnector:
        row = postgres_client.fetch_one(
            """
            SELECT
              id::text AS id,
              name,
                            provider,
                            model,
              provider_label,
              api_key_encrypted
            FROM plant_genie_ai_connectors
            WHERE user_id = %s AND is_active = TRUE
            LIMIT 1
            """,
            (user_id,),
        )
        if row is None:
            raise PlantGenieConnectorNotConfiguredError(
                "No active AI connector is configured. Open Settings > AI Connectors and activate one before using Plant Genie."
            )

        return PlantGenieActiveConnector(
            id=str(row["id"]),
            name=str(row["name"]),
            provider=str(row["provider"]),
            model=_normalize_optional_text(row.get("model")),
            api_key=plant_genie_secret_store.decrypt(str(row["api_key_encrypted"])),
            provider_label=row.get("provider_label"),
        )

    def query_active_connector(
        self,
        user_id: str,
        prompt: str,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_prompt = str(prompt or "").strip()
        if not normalized_prompt:
            raise ValueError("prompt is required")

        connector = self.get_active_connector(user_id)
        request_context = dict(context or {})
        selected_tag = request_context.get("selected_tag") if isinstance(request_context.get("selected_tag"), str) else None
        binding_config = plant_genie_ai_binding_service.get_binding_config(user_id)
        request_context["live_plant_data"] = plant_genie_plant_data_runtime.build_query_context(
            user_id,
            selected_tag=selected_tag,
            binding_config=binding_config,
        )
        response_payload = self._invoke_connector(connector, normalized_prompt, request_context)
        answer = self._extract_answer_text(response_payload)
        timestamp = _utc_now()
        return {
            "success": True,
            "answer": answer,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "provider_label": connector.provider_label,
            "timestamp": timestamp,
        }

    @classmethod
    def _probe_connector(cls, connector: PlantGenieActiveConnector) -> tuple[bool, str]:
        provider_config = resolve_plant_genie_ai_provider_config(connector.provider)
        resolved_connector = cls._with_resolved_model(connector, provider_config.default_model)
        endpoint_url = build_plant_genie_provider_endpoint(provider_config, model=resolved_connector.model)
        headers = cls._build_request_headers(provider_config.auth_scheme, connector.api_key)
        headers["X-Plant-Genie-Test"] = "true"

        for method in ("HEAD", "GET"):
            request = urllib_request.Request(endpoint_url, headers=headers, method=method)
            try:
                with urllib_request.urlopen(request, timeout=8) as response:
                    status_code = getattr(response, "status", 200)
                    return True, f"Endpoint reachable via {method} (HTTP {status_code})."
            except urllib_error.HTTPError as exc:
                if exc.code == 405 and method == "HEAD":
                    continue
                if exc.code >= 500:
                    return False, f"Endpoint responded with server error HTTP {exc.code}."
                return True, f"Endpoint reachable via {method} (HTTP {exc.code})."
            except urllib_error.URLError as exc:
                return False, f"Endpoint unreachable: {exc.reason}"
            except Exception as exc:
                return False, f"Endpoint test failed: {exc}"

        return False, "Endpoint did not respond to supported test methods."

    @classmethod
    def _invoke_connector(
        cls,
        connector: PlantGenieActiveConnector,
        prompt: str,
        context: Mapping[str, Any],
    ) -> Any:
        provider_config = resolve_plant_genie_ai_provider_config(connector.provider)
        resolved_connector = cls._with_resolved_model(connector, provider_config.default_model)
        adapter = cls._resolve_provider_adapter(resolved_connector.provider)
        try:
            payload = adapter.build_payload(connector=resolved_connector, prompt=prompt, context=context)
        except ValueError as exc:
            raise PlantGenieConnectorInvocationError(str(exc)) from exc

        endpoint_url = build_plant_genie_provider_endpoint(provider_config, model=resolved_connector.model)
        body = json.dumps(payload).encode("utf-8")
        request = urllib_request.Request(
            endpoint_url,
            data=body,
            headers=cls._build_request_headers(
                provider_config.auth_scheme,
                connector.api_key,
                include_content_headers=True,
            ),
            method="POST",
        )

        try:
            with urllib_request.urlopen(request, timeout=45) as response:
                raw_body = response.read().decode("utf-8", errors="replace").strip()
                if not raw_body:
                    raise PlantGenieConnectorInvocationError(
                        f"Connector '{connector.name}' returned an empty response body."
                    )

                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type.lower() or raw_body[:1] in {"{", "["}:
                    try:
                        return json.loads(raw_body)
                    except json.JSONDecodeError as exc:
                        raise PlantGenieConnectorInvocationError(
                            f"Connector '{connector.name}' returned malformed JSON."
                        ) from exc

                return {"answer": raw_body}
        except urllib_error.HTTPError as exc:
            detail = cls._extract_remote_error_detail(exc)
            hint = " Check the configured endpoint and API key permissions." if exc.code in {401, 403} else ""
            raise PlantGenieConnectorInvocationError(
                f"Connector '{connector.name}' request failed with HTTP {exc.code}. {detail}{hint}".strip()
            ) from exc
        except urllib_error.URLError as exc:
            raise PlantGenieConnectorInvocationError(
                f"Connector '{connector.name}' is unreachable: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise PlantGenieConnectorInvocationError(
                f"Connector '{connector.name}' timed out while generating a response."
            ) from exc
        except PlantGenieConnectorInvocationError:
            raise
        except Exception as exc:
            raise PlantGenieConnectorInvocationError(
                f"Connector '{connector.name}' request failed: {exc}"
            ) from exc

    @staticmethod
    def _resolve_provider_adapter(provider: PlantGenieAIProvider) -> PlantGenieProviderAdapter:
        if provider == "anthropic":
            return AnthropicMessagesAdapter()
        if provider in {"openai", "azure_openai", "openrouter"}:
            return OpenAICompatibleChatCompletionsAdapter()
        raise PlantGenieConnectorInvocationError("Unsupported Plant Genie AI provider.")

    @staticmethod
    def _build_request_headers(auth_scheme: str, api_key: str, *, include_content_headers: bool = False) -> dict[str, str]:
        headers = {
            "User-Agent": "CrossLayerX-Plant-Genie/1.0",
        }
        if include_content_headers:
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json, text/plain;q=0.9, */*;q=0.8"

        if auth_scheme == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            return headers

        if auth_scheme == "azure_api_key":
            headers["api-key"] = api_key
            return headers

        headers["Authorization"] = f"Bearer {api_key}"
        return headers

    @staticmethod
    def _with_resolved_model(connector: PlantGenieActiveConnector, default_model: str | None) -> PlantGenieActiveConnector:
        if connector.model:
            return connector
        normalized_default = _normalize_optional_text(default_model)
        if not normalized_default:
            return connector
        return replace(connector, model=normalized_default)

    @classmethod
    def _extract_answer_text(cls, payload: Any) -> str:
        text = cls._extract_text_candidate(payload)
        if text:
            return text
        raise PlantGenieConnectorInvocationError(
            "The active connector responded successfully, but no readable answer was found in the payload."
        )

    @classmethod
    def _extract_text_candidate(cls, value: Any) -> str | None:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None

        if isinstance(value, list):
            parts = [text for item in value if (text := cls._extract_text_candidate(item))]
            if parts:
                return "\n\n".join(parts)
            return None

        if isinstance(value, Mapping):
            for key in ("answer", "response", "output_text", "generated_text", "completion", "text"):
                candidate = cls._extract_text_candidate(value.get(key))
                if candidate:
                    return candidate

            message = value.get("message")
            if isinstance(message, Mapping):
                candidate = cls._extract_text_candidate(message.get("content"))
                if candidate:
                    return candidate
            else:
                candidate = cls._extract_text_candidate(message)
                if candidate:
                    return candidate

            content = value.get("content")
            candidate = cls._extract_text_candidate(content)
            if candidate:
                return candidate

            choices = value.get("choices")
            if isinstance(choices, list):
                for choice in choices:
                    candidate = cls._extract_text_candidate(choice)
                    if candidate:
                        return candidate

            for key in ("output", "result", "data", "delta"):
                candidate = cls._extract_text_candidate(value.get(key))
                if candidate:
                    return candidate

        return None

    @staticmethod
    def _extract_remote_error_detail(error: urllib_error.HTTPError) -> str:
        try:
            raw_body = error.read().decode("utf-8", errors="replace").strip()
        except Exception:
            raw_body = ""

        if not raw_body:
            return "The remote endpoint did not provide any error details."

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            return raw_body[:500]

        if isinstance(parsed, Mapping):
            for key in ("detail", "error", "message"):
                value = parsed.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return raw_body[:500]

    def _get_connector_row(self, user_id: str, connector_id: str, include_secret: bool) -> dict[str, Any]:
        secret_column = ", api_key_encrypted" if include_secret else ""
        row = postgres_client.fetch_one(
            f"""
            SELECT
              id::text AS id,
              name,
                            provider,
                            model,
              provider_label,
              notes,
              is_active,
              health_status,
              health_message,
              last_tested_at,
              created_at,
              updated_at
              {secret_column}
            FROM plant_genie_ai_connectors
            WHERE id = %s::uuid AND user_id = %s
            LIMIT 1
            """,
            (connector_id, user_id),
        )
        if row is None:
            raise KeyError(connector_id)
        return row

    @staticmethod
    def _row_to_active_connector(row: dict[str, Any]) -> PlantGenieActiveConnector:
        return PlantGenieActiveConnector(
            id=str(row["id"]),
            name=str(row["name"]),
            provider=str(row["provider"]),
            model=_normalize_optional_text(row.get("model")),
            api_key=plant_genie_secret_store.decrypt(str(row["api_key_encrypted"])),
            provider_label=row.get("provider_label"),
        )

    @staticmethod
    def _row_to_response(row: dict[str, Any]) -> PlantGenieAIConnectorResponse:
        return PlantGenieAIConnectorResponse(
            id=str(row["id"]),
            name=str(row["name"]),
            provider=str(row["provider"]),
            model=_normalize_optional_text(row.get("model")),
            provider_label=row.get("provider_label"),
            notes=row.get("notes"),
            has_api_key=True,
            is_active=bool(row.get("is_active", False)),
            health_status=str(row.get("health_status") or "unknown"),
            health_message=row.get("health_message"),
            last_tested_at=row.get("last_tested_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


plant_genie_connector_service = PlantGenieConnectorService()