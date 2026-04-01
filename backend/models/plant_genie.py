from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Literal, cast, get_args
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


PlantGenieConnectorHealthStatus = Literal["unknown", "healthy", "unhealthy"]
PlantGenieSupportedAIProvider = Literal[
    "openai",
    "anthropic",
    "azure_openai",
    "openrouter",
]
PlantGenieAIProvider = Literal[
    "openai",
    "anthropic",
    "azure_openai",
    "openrouter",
    "custom_openai_compatible",
]

_SUPPORTED_AI_PROVIDERS = set(get_args(PlantGenieSupportedAIProvider))


def _normalize_required_text(value: str, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_supported_ai_provider(value: Any) -> PlantGenieSupportedAIProvider:
    normalized = _normalize_required_text(str(value or ""), "provider").lower().replace("-", "_").replace(" ", "_")
    if normalized not in _SUPPORTED_AI_PROVIDERS:
        supported = ", ".join(sorted(_SUPPORTED_AI_PROVIDERS))
        raise ValueError(f"provider must be one of: {supported}")
    return cast(PlantGenieSupportedAIProvider, normalized)


def _validate_url_with_schemes(value: str, field_name: str, allowed_schemes: set[str]) -> str:
    normalized = _normalize_required_text(value, field_name)
    parsed = urlparse(normalized)
    if parsed.scheme not in allowed_schemes or not parsed.netloc:
        supported = ", ".join(sorted(allowed_schemes))
        raise ValueError(f"{field_name} must be a valid URL using one of these schemes: {supported}")
    return normalized


def _validate_endpoint_url(value: str) -> str:
    return _validate_url_with_schemes(value, "endpoint_url", {"http", "https"})


def _validate_opcua_server_url(value: str) -> str:
    return _validate_url_with_schemes(value, "config.server_url", {"opc.tcp", "http", "https"})


def _extract_node_ids_from_subscription_config(value: Any) -> list[str]:
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return _normalize_string_list(value, "config.subscription_config")
        extracted = [
            str(item.get("node_id") or item.get("nodeId") or "").strip()
            for item in value
            if isinstance(item, dict)
        ]
        return _normalize_string_list(extracted, "config.subscription_config")

    if isinstance(value, dict):
        for key in ("node_ids", "nodeIds", "subscriptions", "nodes"):
            nested = value.get(key)
            if nested is None:
                continue
            return _extract_node_ids_from_subscription_config(nested)

    raise ValueError("config.subscription_config must define at least one node identifier")


class PlantGenieAIConnectorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=1, max_length=4096)
    model: str | None = Field(default=None, max_length=240)
    provider_label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _normalize_required_text(value, "name")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        return _normalize_required_text(value, "api_key")

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("provider_label", "notes")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PlantGenieAIConnectorUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    api_key: str | None = Field(default=None, max_length=4096)
    model: str | None = Field(default=None, max_length=240)
    provider_label: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _normalize_required_text(value, "name")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("model")
    @classmethod
    def validate_update_model(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("provider_label", "notes")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PlantGenieAIConnectorResponse(BaseModel):
    id: str
    name: str
    provider: PlantGenieAIProvider
    model: str | None = None
    provider_label: str | None = None
    notes: str | None = None
    has_api_key: bool = True
    is_active: bool = False
    health_status: PlantGenieConnectorHealthStatus = "unknown"
    health_message: str | None = None
    last_tested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PlantGenieAIConnectorListResponse(BaseModel):
    connectors: list[PlantGenieAIConnectorResponse] = Field(default_factory=list)


class PlantGenieAIConnectorDeleteResponse(BaseModel):
    success: bool = True
    message: str


class PlantGenieAIConnectorTestResponse(BaseModel):
    success: bool
    message: str
    connector: PlantGenieAIConnectorResponse


class PlantGenieQueryContext(BaseModel):
    has_project: bool = False
    project_name: str | None = Field(default=None, max_length=240)
    selected_tag: str | None = Field(default=None, max_length=240)

    @field_validator("project_name", "selected_tag")
    @classmethod
    def validate_optional_context_text(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PlantGenieQueryRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=16000)
    context: PlantGenieQueryContext = Field(default_factory=PlantGenieQueryContext)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        return _normalize_required_text(value, "prompt")


class PlantGenieQueryResponse(BaseModel):
    success: bool = True
    answer: str
    connector_id: str
    connector_name: str
    provider_label: str | None = None
    timestamp: datetime


PlantGeniePlantDataConnectorType = Literal["opcua", "mqtt", "sql"]


def _normalize_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized = [str(item).strip() for item in value if str(item).strip()]
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class PlantGeniePlantDataConnectorRuntimeState(BaseModel):
    enabled: bool = False
    running: bool = False
    healthy: bool = False
    last_update: datetime | None = None
    last_error: str | None = None


class PlantGeniePlantDataConnectorHealth(BaseModel):
    id: str
    healthy: bool = False
    lastUpdate: datetime | None = None


class PlantGeniePlantDataConnectorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    connector_type: PlantGeniePlantDataConnectorType
    poll_interval_ms: int = Field(default=5000, ge=500, le=300000)
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_connector_name(cls, value: str) -> str:
        return _normalize_required_text(value, "name")

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("config")
    @classmethod
    def validate_create_config(cls, value: dict[str, Any], info) -> dict[str, Any]:
        connector_type = info.data.get("connector_type")
        if connector_type:
            return _validate_plant_data_connector_config(connector_type, value)
        return value

    @field_validator("secrets")
    @classmethod
    def validate_create_secrets(cls, value: dict[str, Any], info) -> dict[str, Any]:
        connector_type = info.data.get("connector_type")
        if connector_type:
            return _validate_plant_data_connector_secrets(connector_type, value)
        return value


class PlantGeniePlantDataConnectorUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    connector_type: PlantGeniePlantDataConnectorType
    poll_interval_ms: int = Field(default=5000, ge=500, le=300000)
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_update_name(cls, value: str) -> str:
        return _normalize_required_text(value, "name")

    @field_validator("connector_type")
    @classmethod
    def validate_update_connector_type(cls, value: PlantGeniePlantDataConnectorType) -> PlantGeniePlantDataConnectorType:
        return value

    @field_validator("config", "secrets")
    @classmethod
    def validate_update_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value


class PlantGeniePlantDataConnectorResponse(BaseModel):
    id: str
    name: str
    connector_type: PlantGeniePlantDataConnectorType
    poll_interval_ms: int
    config: dict[str, Any] = Field(default_factory=dict)
    has_secrets: bool = False
    runtime: PlantGeniePlantDataConnectorRuntimeState = Field(default_factory=PlantGeniePlantDataConnectorRuntimeState)
    health: PlantGeniePlantDataConnectorHealth
    last_tested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PlantGeniePlantDataConnectorListResponse(BaseModel):
    connectors: list[PlantGeniePlantDataConnectorResponse] = Field(default_factory=list)


class PlantGeniePlantDataConnectorDeleteResponse(BaseModel):
    success: bool = True
    message: str


class PlantGeniePlantDataConnectorTestResponse(BaseModel):
    success: bool
    message: str
    connector: PlantGeniePlantDataConnectorResponse


def _validate_plant_data_connector_config(
    connector_type: PlantGeniePlantDataConnectorType,
    config: dict[str, Any],
) -> dict[str, Any]:
    if connector_type == "opcua":
        endpoint = _validate_opcua_server_url(str(config.get("endpoint") or config.get("server_url") or ""))
        subscription_config = config.get("subscription_config")
        raw_node_config = _normalize_optional_text(config.get("node_config"))
        node_ids_source = config.get("node_ids") or []
        if subscription_config is not None and not node_ids_source:
            node_ids_source = _extract_node_ids_from_subscription_config(subscription_config)
        if raw_node_config and not node_ids_source:
            try:
                parsed = json.loads(raw_node_config)
                if isinstance(parsed, list):
                    node_ids_source = parsed
            except Exception:
                node_ids_source = [segment.strip() for segment in raw_node_config.replace("\n", ",").split(",")]
        node_ids = _normalize_string_list(node_ids_source, "config.node_ids")
        return {
            "server_url": endpoint,
            "endpoint": endpoint,
            "node_ids": node_ids,
            "subscription_config": subscription_config if subscription_config is not None else node_ids,
            "node_config": raw_node_config or json.dumps(node_ids),
            "security_mode": _normalize_optional_text(config.get("security_mode") or config.get("security_policy")),
            "username": _normalize_optional_text(config.get("username")),
        }

    if connector_type == "mqtt":
        broker_url = _normalize_optional_text(config.get("broker_url"))
        if broker_url:
            normalized_broker_url = broker_url
            if "://" not in normalized_broker_url:
                normalized_broker_url = f"mqtt://{normalized_broker_url}"
            parsed = urlparse(normalized_broker_url)
            host = _normalize_required_text(parsed.hostname or "", "config.broker_url")
            port = int(parsed.port or config.get("port") or 1883)
            broker_url = f"{parsed.scheme or 'mqtt'}://{host}:{port}"
        else:
            host = _normalize_required_text(str(config.get("host") or ""), "config.host")
            port = int(config.get("port") or 1883)
            broker_url = f"mqtt://{host}:{port}"
        topic = _normalize_required_text(str(config.get("topic") or ""), "config.topic")
        qos = int(config.get("qos") or 0)
        if port <= 0 or port > 65535:
            raise ValueError("config.port must be between 1 and 65535")
        if qos < 0 or qos > 2:
            raise ValueError("config.qos must be between 0 and 2")
        return {
            "broker_url": broker_url,
            "host": host,
            "port": port,
            "topic": topic,
            "client_id": _normalize_optional_text(config.get("client_id")),
            "username": _normalize_optional_text(config.get("username")),
            "qos": qos,
        }

    host = _normalize_required_text(str(config.get("host") or ""), "config.host")
    port = int(config.get("port") or 5432)
    if port <= 0 or port > 65535:
        raise ValueError("config.port must be between 1 and 65535")
    database = _normalize_required_text(str(config.get("database") or ""), "config.database")
    username = _normalize_required_text(str(config.get("username") or ""), "config.username")
    query = _normalize_required_text(str(config.get("query") or ""), "config.query")
    tag_column = _normalize_required_text(str(config.get("tag_column") or config.get("tagColumn") or ""), "config.tag_column")
    value_column = _normalize_required_text(str(config.get("value_column") or config.get("valueColumn") or ""), "config.value_column")
    return {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "query": query,
        "tag_column": tag_column,
        "value_column": value_column,
        "timestamp_column": _normalize_optional_text(config.get("timestamp_column")),
        "driver": _normalize_optional_text(config.get("driver")) or "auto",
    }


def _validate_plant_data_connector_secrets(
    connector_type: PlantGeniePlantDataConnectorType,
    secrets: dict[str, Any],
) -> dict[str, Any]:
    normalized = {str(key): value for key, value in secrets.items() if value is not None and str(key).strip()}
    if connector_type == "sql":
        connection_string = _normalize_optional_text(normalized.get("connection_string"))
        password = _normalize_optional_text(normalized.get("password"))
        if connection_string:
            return {"connection_string": connection_string}
        if password:
            return {"password": password}
        raise ValueError("secrets.password is required")

    password = _normalize_optional_text(normalized.get("password"))
    return {"password": password} if password else {}