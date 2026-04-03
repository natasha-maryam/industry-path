from __future__ import annotations

from datetime import datetime
import json
import re
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


PlantGenieAIBindingTagScope = Literal["all", "selected"]
PlantGenieAIBindingContextMode = Literal["live_only", "historical", "hybrid"]
PlantGenieAIBindingSamplingMode = Literal["stream", "interval"]
PlantGenieAIBindingAccessMode = Literal["read_only", "read_recommend"]

_SUPPORTED_AI_BINDING_TAG_SCOPES = set(get_args(PlantGenieAIBindingTagScope))
_SUPPORTED_AI_BINDING_CONTEXT_MODES = set(get_args(PlantGenieAIBindingContextMode))
_SUPPORTED_AI_BINDING_SAMPLING_MODES = set(get_args(PlantGenieAIBindingSamplingMode))
_SUPPORTED_AI_BINDING_ACCESS_MODES = set(get_args(PlantGenieAIBindingAccessMode))


def _normalize_supported_text_literal(value: Any, field_name: str, supported: set[str]) -> str:
    normalized = _normalize_required_text(str(value or ""), field_name).lower().replace("-", "_").replace(" ", "_")
    if normalized not in supported:
        allowed = ", ".join(sorted(supported))
        raise ValueError(f"{field_name} must be one of: {allowed}")
    return normalized


def _normalize_optional_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return [str(item).strip() for item in value if str(item).strip()]


class PlantGenieAIBindingRequest(BaseModel):
    data_source_connector_id: str = Field(min_length=1, max_length=120)
    tag_scope: PlantGenieAIBindingTagScope = "all"
    selected_tags: list[str] = Field(default_factory=list)
    context_mode: PlantGenieAIBindingContextMode = "live_only"
    sampling_mode: PlantGenieAIBindingSamplingMode = "stream"
    sampling_interval_ms: int | None = Field(default=None, ge=500, le=300000)
    ai_access_mode: PlantGenieAIBindingAccessMode = "read_only"
    include_system_structure: bool = False
    ai_api_input: str | None = Field(default=None, max_length=4000)

    @field_validator("data_source_connector_id")
    @classmethod
    def validate_data_source_connector_id(cls, value: str) -> str:
        return _normalize_required_text(value, "data_source_connector_id")

    @field_validator("tag_scope")
    @classmethod
    def validate_tag_scope(cls, value: PlantGenieAIBindingTagScope) -> PlantGenieAIBindingTagScope:
        normalized = _normalize_supported_text_literal(value, "tag_scope", _SUPPORTED_AI_BINDING_TAG_SCOPES)
        return cast(PlantGenieAIBindingTagScope, normalized)

    @field_validator("selected_tags")
    @classmethod
    def validate_selected_tags(cls, value: list[str]) -> list[str]:
        return _normalize_optional_string_list(value, "selected_tags")

    @field_validator("context_mode")
    @classmethod
    def validate_context_mode(cls, value: PlantGenieAIBindingContextMode) -> PlantGenieAIBindingContextMode:
        normalized = _normalize_supported_text_literal(value, "context_mode", _SUPPORTED_AI_BINDING_CONTEXT_MODES)
        return cast(PlantGenieAIBindingContextMode, normalized)

    @field_validator("sampling_mode")
    @classmethod
    def validate_sampling_mode(cls, value: PlantGenieAIBindingSamplingMode) -> PlantGenieAIBindingSamplingMode:
        normalized = _normalize_supported_text_literal(value, "sampling_mode", _SUPPORTED_AI_BINDING_SAMPLING_MODES)
        return cast(PlantGenieAIBindingSamplingMode, normalized)

    @field_validator("ai_access_mode")
    @classmethod
    def validate_ai_access_mode(cls, value: PlantGenieAIBindingAccessMode) -> PlantGenieAIBindingAccessMode:
        normalized = _normalize_supported_text_literal(value, "ai_access_mode", _SUPPORTED_AI_BINDING_ACCESS_MODES)
        return cast(PlantGenieAIBindingAccessMode, normalized)

    @field_validator("ai_api_input")
    @classmethod
    def validate_ai_api_input(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("sampling_interval_ms")
    @classmethod
    def validate_sampling_interval_ms(cls, value: int | None) -> int | None:
        return value

    def model_post_init(self, __context: Any) -> None:
        if self.tag_scope == "selected" and not self.selected_tags:
            raise ValueError("selected_tags must not be empty when tag_scope is selected")
        if self.sampling_mode == "interval" and self.sampling_interval_ms is None:
            raise ValueError("sampling_interval_ms is required when sampling_mode is interval")


class PlantGenieAIBindingResponse(BaseModel):
    configured: bool = False
    data_source_connector_id: str | None = None
    data_source_connector_name: str | None = None
    tag_scope: PlantGenieAIBindingTagScope = "all"
    selected_tags: list[str] = Field(default_factory=list)
    context_mode: PlantGenieAIBindingContextMode = "live_only"
    sampling_mode: PlantGenieAIBindingSamplingMode = "stream"
    sampling_interval_ms: int | None = None
    ai_access_mode: PlantGenieAIBindingAccessMode = "read_only"
    include_system_structure: bool = False
    ai_api_input: str | None = None
    source_connector_enabled: bool = False
    source_connector_healthy: bool = False
    updated_at: datetime | None = None


class PlantGenieAIBindingConnectResponse(BaseModel):
    success: bool = True
    message: str
    binding: PlantGenieAIBindingResponse


PlantGeniePlantDataConnectorType = Literal["opcua", "mqtt", "sql", "modbus_tcp", "historian"]
PlantGeniePlantDataOPCUASecurityMode = Literal["sign", "sign_and_encrypt"]
PlantGeniePlantDataOPCUASecurityPolicy = Literal["basic256sha256", "aes128sha256rsaoaep", "aes256sha256rsapss"]
PlantGeniePlantDataOPCUAAuthMode = Literal["anonymous", "username_password", "certificate"]
PlantGeniePlantDataSQLDBType = Literal["postgresql", "mysql", "sqlserver"]
PlantGeniePlantDataSQLQueryMode = Literal["table", "custom_query"]
PlantGeniePlantDataSQLRefreshMode = Literal["latest_row", "full_snapshot"]
PlantGeniePlantDataModbusRegisterType = Literal["coil", "discrete_input", "holding_register", "input_register"]
PlantGeniePlantDataModbusDataType = Literal["bool", "uint16", "int16", "uint32", "int32", "float32", "uint64", "int64", "float64", "string"]
PlantGeniePlantDataModbusEndianness = Literal["big", "little"]
PlantGeniePlantDataModbusWriteFunctionCode = Literal["fc5", "fc6", "fc16"]
PlantGeniePlantDataHistorianSubtype = Literal["osisoft_pi", "generic_timeseries"]
PlantGeniePlantDataHistorianGenericMode = Literal["sql", "rest"]
PlantGeniePlantDataHistorianAuthMode = Literal["anonymous", "basic", "bearer"]
PlantGeniePlantDataHistorianRetrievalMode = Literal["snapshot", "recorded", "interpolated", "summary"]
PlantGeniePlantDataHistorianTimeRangeUnit = Literal["minutes", "hours", "days"]

_SUPPORTED_OPCUA_SECURITY_MODES = set(get_args(PlantGeniePlantDataOPCUASecurityMode))
_SUPPORTED_OPCUA_SECURITY_POLICIES = set(get_args(PlantGeniePlantDataOPCUASecurityPolicy))
_SUPPORTED_OPCUA_AUTH_MODES = set(get_args(PlantGeniePlantDataOPCUAAuthMode))
_SUPPORTED_SQL_DB_TYPES = set(get_args(PlantGeniePlantDataSQLDBType))
_SUPPORTED_SQL_QUERY_MODES = set(get_args(PlantGeniePlantDataSQLQueryMode))
_SUPPORTED_SQL_REFRESH_MODES = set(get_args(PlantGeniePlantDataSQLRefreshMode))
_SUPPORTED_MODBUS_REGISTER_TYPES = set(get_args(PlantGeniePlantDataModbusRegisterType))
_SUPPORTED_MODBUS_DATA_TYPES = set(get_args(PlantGeniePlantDataModbusDataType))
_SUPPORTED_MODBUS_ENDIANNESS = set(get_args(PlantGeniePlantDataModbusEndianness))
_SUPPORTED_MODBUS_WRITE_FUNCTION_CODES = set(get_args(PlantGeniePlantDataModbusWriteFunctionCode))
_SUPPORTED_HISTORIAN_SUBTYPES = set(get_args(PlantGeniePlantDataHistorianSubtype))
_SUPPORTED_HISTORIAN_GENERIC_MODES = set(get_args(PlantGeniePlantDataHistorianGenericMode))
_SUPPORTED_HISTORIAN_AUTH_MODES = set(get_args(PlantGeniePlantDataHistorianAuthMode))
_SUPPORTED_HISTORIAN_RETRIEVAL_MODES = set(get_args(PlantGeniePlantDataHistorianRetrievalMode))
_SUPPORTED_HISTORIAN_TIME_RANGE_UNITS = set(get_args(PlantGeniePlantDataHistorianTimeRangeUnit))


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


class PlantGeniePlantDataOPCUABrowseNodeResponse(BaseModel):
    node_id: str
    browse_name: str
    display_name: str
    node_class: str
    has_children: bool = False
    selectable: bool = False


class PlantGeniePlantDataOPCUABrowseResponse(BaseModel):
    node_id: str
    browse_name: str
    display_name: str
    nodes: list[PlantGeniePlantDataOPCUABrowseNodeResponse] = Field(default_factory=list)


class PlantGeniePlantDataOPCUABrowseRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)
    node_id: str | None = Field(default=None, max_length=1024)

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("config")
    @classmethod
    def validate_browse_config(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_config("opcua", value, require_node_ids=False)

    @field_validator("secrets")
    @classmethod
    def validate_browse_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_secrets("opcua", value)

    @field_validator("node_id")
    @classmethod
    def validate_node_id(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class PlantGeniePlantDataSQLSchemaRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)
    table_name: str | None = Field(default=None, max_length=256)
    table_schema: str | None = Field(default=None, max_length=256)

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("secrets")
    @classmethod
    def validate_schema_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_secrets("sql", value)


class PlantGeniePlantDataSQLTableResponse(BaseModel):
    schema: str
    name: str
    label: str


class PlantGeniePlantDataSQLColumnResponse(BaseModel):
    name: str
    data_type: str


class PlantGeniePlantDataSQLSchemaResponse(BaseModel):
    tables: list[PlantGeniePlantDataSQLTableResponse] = Field(default_factory=list)
    columns: list[PlantGeniePlantDataSQLColumnResponse] = Field(default_factory=list)


class PlantGeniePlantDataSQLPreviewRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=25, ge=1, le=100)

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("secrets")
    @classmethod
    def validate_preview_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_secrets("sql", value)


class PlantGeniePlantDataSQLPreviewResponse(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0


class PlantGeniePlantDataModbusPreviewRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("config")
    @classmethod
    def validate_preview_config(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_config("modbus_tcp", value)

    @field_validator("secrets")
    @classmethod
    def validate_preview_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_secrets("modbus_tcp", value)


class PlantGeniePlantDataModbusPreviewResponse(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0


class PlantGeniePlantDataHistorianBrowseItemResponse(BaseModel):
    web_id: str
    label: str
    path: str
    item_type: str


class PlantGeniePlantDataHistorianBrowseRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)
    query: str | None = Field(default=None, max_length=256)
    limit: int = Field(default=50, ge=1, le=200)

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("config")
    @classmethod
    def validate_browse_config(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_config("historian", value)

    @field_validator("secrets")
    @classmethod
    def validate_browse_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_secrets("historian", value)


class PlantGeniePlantDataHistorianBrowseResponse(BaseModel):
    items: list[PlantGeniePlantDataHistorianBrowseItemResponse] = Field(default_factory=list)


class PlantGeniePlantDataHistorianPreviewRequest(BaseModel):
    config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] = Field(default_factory=dict)

    @field_validator("config", "secrets")
    @classmethod
    def validate_mapping_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("config and secrets must be objects")
        return value

    @field_validator("config")
    @classmethod
    def validate_preview_config(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_config("historian", value)

    @field_validator("secrets")
    @classmethod
    def validate_preview_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_plant_data_connector_secrets("historian", value)


class PlantGeniePlantDataHistorianPreviewResponse(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0


def _normalize_optional_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_sql_db_type(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "postgresql"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_SQL_DB_TYPES:
        supported = ", ".join(sorted(_SUPPORTED_SQL_DB_TYPES))
        raise ValueError(f"config.db_type must be one of: {supported}")
    return normalized


def _normalize_sql_query_mode(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "table"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_SQL_QUERY_MODES:
        supported = ", ".join(sorted(_SUPPORTED_SQL_QUERY_MODES))
        raise ValueError(f"config.query_mode must be one of: {supported}")
    return normalized


def _normalize_sql_refresh_mode(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "latest_row"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_SQL_REFRESH_MODES:
        supported = ", ".join(sorted(_SUPPORTED_SQL_REFRESH_MODES))
        raise ValueError(f"config.refresh_mode must be one of: {supported}")
    return normalized


def _normalize_sql_tag_mappings(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("config.tag_mappings must be a list")
    normalized: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("config.tag_mappings items must be objects")
        source_column = _normalize_required_text(
            str(item.get("source_column") or item.get("sourceColumn") or ""),
            "config.tag_mappings.source_column",
        )
        target_tag = _normalize_required_text(
            str(item.get("target_tag") or item.get("targetTag") or ""),
            "config.tag_mappings.target_tag",
        )
        normalized.append({"source_column": source_column, "target_tag": target_tag})
    return normalized


def _normalize_modbus_register_type(value: Any) -> str:
    normalized = _normalize_required_text(str(value or ""), "config.tag_mappings.register_type").lower()
    if normalized not in _SUPPORTED_MODBUS_REGISTER_TYPES:
        supported = ", ".join(sorted(_SUPPORTED_MODBUS_REGISTER_TYPES))
        raise ValueError(f"config.tag_mappings.register_type must be one of: {supported}")
    return normalized


def _normalize_modbus_data_type(value: Any) -> str:
    normalized = _normalize_required_text(str(value or ""), "config.tag_mappings.data_type").lower()
    if normalized not in _SUPPORTED_MODBUS_DATA_TYPES:
        supported = ", ".join(sorted(_SUPPORTED_MODBUS_DATA_TYPES))
        raise ValueError(f"config.tag_mappings.data_type must be one of: {supported}")
    return normalized


def _normalize_modbus_endianness(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "big"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_MODBUS_ENDIANNESS:
        supported = ", ".join(sorted(_SUPPORTED_MODBUS_ENDIANNESS))
        raise ValueError(f"config.tag_mappings.endianness must be one of: {supported}")
    return normalized


def _normalize_modbus_write_function_code(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "fc6"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_MODBUS_WRITE_FUNCTION_CODES:
        supported = ", ".join(sorted(_SUPPORTED_MODBUS_WRITE_FUNCTION_CODES))
        raise ValueError(f"config.write_function_code must be one of: {supported}")
    return normalized


def _normalize_historian_subtype(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "osisoft_pi"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_HISTORIAN_SUBTYPES:
        supported = ", ".join(sorted(_SUPPORTED_HISTORIAN_SUBTYPES))
        raise ValueError(f"config.historian_subtype must be one of: {supported}")
    return normalized


def _normalize_historian_generic_mode(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "sql"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_HISTORIAN_GENERIC_MODES:
        supported = ", ".join(sorted(_SUPPORTED_HISTORIAN_GENERIC_MODES))
        raise ValueError(f"config.generic_mode must be one of: {supported}")
    return normalized


def _normalize_historian_auth_mode(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "anonymous"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_HISTORIAN_AUTH_MODES:
        supported = ", ".join(sorted(_SUPPORTED_HISTORIAN_AUTH_MODES))
        raise ValueError(f"config.authentication_mode must be one of: {supported}")
    return normalized


def _normalize_historian_retrieval_mode(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "snapshot"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_HISTORIAN_RETRIEVAL_MODES:
        supported = ", ".join(sorted(_SUPPORTED_HISTORIAN_RETRIEVAL_MODES))
        raise ValueError(f"config.retrieval_mode must be one of: {supported}")
    return normalized


def _normalize_historian_time_range_unit(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "hours"
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_HISTORIAN_TIME_RANGE_UNITS:
        supported = ", ".join(sorted(_SUPPORTED_HISTORIAN_TIME_RANGE_UNITS))
        raise ValueError(f"config.time_range_unit must be one of: {supported}")
    return normalized


def _normalize_historian_pi_tag_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("config.tag_mappings must include at least one historian mapping")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("config.tag_mappings items must be objects")
        internal_tag = _normalize_required_text(str(item.get("internal_tag") or item.get("internalTag") or ""), "config.tag_mappings.internal_tag")
        web_id = _normalize_optional_text(item.get("web_id") or item.get("webId"))
        manual_path = _normalize_optional_text(item.get("manual_path") or item.get("manualPath"))
        display_path = _normalize_optional_text(item.get("display_path") or item.get("displayPath"))
        if not web_id and not manual_path:
            raise ValueError("config.tag_mappings entries must include a web_id or manual_path")
        normalized.append(
            {
                "internal_tag": internal_tag,
                "web_id": web_id,
                "manual_path": manual_path,
                "display_path": display_path,
            }
        )
    return normalized


def _normalize_modbus_tag_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("config.tag_mappings must be a list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("config.tag_mappings items must be objects")
        register_type = _normalize_modbus_register_type(item.get("register_type") or item.get("registerType"))
        address = int(item.get("address") or 0)
        quantity = int(item.get("quantity") or 1)
        data_type = _normalize_modbus_data_type(item.get("data_type") or item.get("dataType"))
        endianness = _normalize_modbus_endianness(item.get("endianness"))
        internal_tag = _normalize_required_text(str(item.get("internal_tag") or item.get("internalTag") or ""), "config.tag_mappings.internal_tag")
        multiplier = float(item.get("multiplier") or 1.0)
        offset = float(item.get("offset") or 0.0)
        engineering_units = _normalize_optional_text(item.get("engineering_units") or item.get("engineeringUnits"))
        writable = bool(item.get("writable"))
        word_swap = bool(item.get("word_swap") or item.get("wordSwap"))
        if address < 0 or address > 65535:
            raise ValueError("config.tag_mappings.address must be between 0 and 65535")
        if quantity < 1 or quantity > 125:
            raise ValueError("config.tag_mappings.quantity must be between 1 and 125")
        if register_type in {"coil", "discrete_input"} and data_type != "bool":
            raise ValueError("coil and discrete_input mappings must use bool data_type")
        if writable and register_type not in {"coil", "holding_register"}:
            raise ValueError("Only coil and holding_register mappings can be writable")
        normalized.append(
            {
                "register_type": register_type,
                "address": address,
                "quantity": quantity,
                "data_type": data_type,
                "endianness": endianness,
                "word_swap": word_swap,
                "internal_tag": internal_tag,
                "multiplier": multiplier,
                "offset": offset,
                "engineering_units": engineering_units,
                "writable": writable,
            }
        )
    if not normalized:
        raise ValueError("config.tag_mappings must include at least one register mapping")
    return normalized


def _normalize_opcua_security_mode(value: Any) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None or normalized.lower() == "none":
        return None
    normalized = normalized.lower()
    if normalized not in _SUPPORTED_OPCUA_SECURITY_MODES:
        supported = ", ".join(sorted(_SUPPORTED_OPCUA_SECURITY_MODES))
        raise ValueError(f"config.security_mode must be one of: {supported}")
    return normalized


def _normalize_opcua_security_policy(value: Any) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    normalized = normalized.lower().replace("-", "").replace("_", "")
    alias_map = {
        "basic256sha256": "basic256sha256",
        "aes128sha256rsaoaep": "aes128sha256rsaoaep",
        "aes256sha256rsapss": "aes256sha256rsapss",
    }
    if normalized not in alias_map:
        supported = ", ".join(sorted(_SUPPORTED_OPCUA_SECURITY_POLICIES))
        raise ValueError(f"config.security_policy must be one of: {supported}")
    return alias_map[normalized]


def _normalize_opcua_auth_mode(value: Any) -> str:
    normalized = _normalize_optional_text(value) or "anonymous"
    normalized = normalized.lower().replace("-", "_").replace("/", "_")
    if normalized not in _SUPPORTED_OPCUA_AUTH_MODES:
        supported = ", ".join(sorted(_SUPPORTED_OPCUA_AUTH_MODES))
        raise ValueError(f"config.authentication_mode must be one of: {supported}")
    return normalized


def _validate_plant_data_connector_config(
    connector_type: PlantGeniePlantDataConnectorType,
    config: dict[str, Any],
    *,
    require_node_ids: bool = True,
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
        node_ids = _normalize_string_list(node_ids_source, "config.node_ids") if node_ids_source or require_node_ids else []
        security_mode = _normalize_opcua_security_mode(config.get("security_mode"))
        security_policy = _normalize_opcua_security_policy(config.get("security_policy"))
        auth_mode = _normalize_opcua_auth_mode(config.get("authentication_mode") or config.get("auth_mode"))
        username = _normalize_optional_text(config.get("username"))
        session_timeout_ms = int(config.get("session_timeout_ms") or 60000)
        if session_timeout_ms < 1000 or session_timeout_ms > 3600000:
            raise ValueError("config.session_timeout_ms must be between 1000 and 3600000")
        trust_list_names = _normalize_optional_string_list(config.get("trust_list_names"), "config.trust_list_names")
        client_certificate_name = _normalize_optional_text(config.get("client_certificate_name"))
        client_private_key_name = _normalize_optional_text(config.get("client_private_key_name"))
        browse_root_node_id = _normalize_optional_text(config.get("browse_root_node_id") or config.get("root_node_id"))
        if security_mode and not security_policy:
            raise ValueError("config.security_policy is required when security_mode is enabled")
        if auth_mode == "username_password" and not username:
            raise ValueError("config.username is required for username_password authentication")
        if (security_mode or auth_mode == "certificate") and (not client_certificate_name or not client_private_key_name):
            raise ValueError("config.client_certificate_name and config.client_private_key_name are required for secure OPC UA sessions")
        return {
            "server_url": endpoint,
            "endpoint": endpoint,
            "node_ids": node_ids,
            "subscription_config": subscription_config if subscription_config is not None else {"nodes": node_ids},
            "node_config": raw_node_config or json.dumps(subscription_config if subscription_config is not None else node_ids),
            "security_mode": security_mode,
            "security_policy": security_policy,
            "authentication_mode": auth_mode,
            "username": username if auth_mode == "username_password" else None,
            "session_timeout_ms": session_timeout_ms,
            "trust_list_names": trust_list_names,
            "client_certificate_name": client_certificate_name,
            "client_private_key_name": client_private_key_name,
            "browse_root_node_id": browse_root_node_id,
        }

    if connector_type == "mqtt":
        broker_url = _normalize_optional_text(config.get("broker_url"))
        tls_enabled = bool(config.get("tls_enabled"))
        if broker_url:
            normalized_broker_url = broker_url
            if "://" not in normalized_broker_url:
                normalized_broker_url = f"mqtt://{normalized_broker_url}"
            parsed = urlparse(normalized_broker_url)
            host = _normalize_required_text(parsed.hostname or "", "config.broker_url")
            port = int(parsed.port or config.get("port") or 1883)
            tls_enabled = tls_enabled or parsed.scheme == "mqtts"
            broker_url = f"{'mqtts' if tls_enabled else 'mqtt'}://{host}:{port}"
        else:
            host = _normalize_required_text(str(config.get("host") or ""), "config.host")
            port = int(config.get("port") or 1883)
            broker_url = f"{'mqtts' if tls_enabled else 'mqtt'}://{host}:{port}"
        topic = _normalize_required_text(str(config.get("topic") or ""), "config.topic")
        qos = int(config.get("qos") or 0)
        keep_alive = int(config.get("keep_alive") or 30)
        if port <= 0 or port > 65535:
            raise ValueError("config.port must be between 1 and 65535")
        if qos < 0 or qos > 2:
            raise ValueError("config.qos must be between 0 and 2")
        if keep_alive < 5 or keep_alive > 3600:
            raise ValueError("config.keep_alive must be between 5 and 3600")
        return {
            "broker_url": broker_url,
            "host": host,
            "port": port,
            "topic": topic,
            "client_id": _normalize_optional_text(config.get("client_id")),
            "username": _normalize_optional_text(config.get("username")),
            "qos": qos,
            "keep_alive": keep_alive,
            "tls_enabled": tls_enabled,
            "certificate_name": _normalize_optional_text(config.get("certificate_name")),
        }

    if connector_type == "modbus_tcp":
        host = _normalize_required_text(str(config.get("host") or ""), "config.host")
        port = int(config.get("port") or 502)
        unit_id = int(config.get("unit_id") or config.get("unitId") or 1)
        timeout_ms = int(config.get("timeout_ms") or config.get("timeoutMs") or 5000)
        retry_attempts = int(config.get("retry_attempts") or config.get("retryAttempts") or 2)
        batch_read = bool(config.get("batch_read"))
        max_registers_per_request = int(config.get("max_registers_per_request") or config.get("maxRegistersPerRequest") or 120)
        enable_write = bool(config.get("enable_write"))
        write_function_code = _normalize_modbus_write_function_code(config.get("write_function_code") or config.get("writeFunctionCode"))
        confirm_before_write = bool(config.get("confirm_before_write"))
        write_rate_limit_ms = int(config.get("write_rate_limit_ms") or config.get("writeRateLimitMs") or 1000)
        tag_mappings = _normalize_modbus_tag_mappings(config.get("tag_mappings") or config.get("tagMappings") or [])
        if port <= 0 or port > 65535:
            raise ValueError("config.port must be between 1 and 65535")
        if unit_id < 0 or unit_id > 255:
            raise ValueError("config.unit_id must be between 0 and 255")
        if timeout_ms < 100 or timeout_ms > 60000:
            raise ValueError("config.timeout_ms must be between 100 and 60000")
        if retry_attempts < 0 or retry_attempts > 10:
            raise ValueError("config.retry_attempts must be between 0 and 10")
        if max_registers_per_request < 1 or max_registers_per_request > 125:
            raise ValueError("config.max_registers_per_request must be between 1 and 125")
        if write_rate_limit_ms < 0 or write_rate_limit_ms > 600000:
            raise ValueError("config.write_rate_limit_ms must be between 0 and 600000")
        writable_mappings = [mapping for mapping in tag_mappings if bool(mapping.get("writable"))]
        if writable_mappings:
            if write_function_code == "fc5" and any(mapping["register_type"] != "coil" for mapping in writable_mappings):
                raise ValueError("config.write_function_code fc5 can only be used with writable coil mappings")
            if write_function_code in {"fc6", "fc16"} and any(mapping["register_type"] != "holding_register" for mapping in writable_mappings):
                raise ValueError("config.write_function_code fc6/fc16 can only be used with writable holding register mappings")
        return {
            "host": host,
            "port": port,
            "unit_id": unit_id,
            "timeout_ms": timeout_ms,
            "retry_attempts": retry_attempts,
            "auto_reconnect": bool(config.get("auto_reconnect", True)),
            "batch_read": batch_read,
            "max_registers_per_request": max_registers_per_request,
            "enable_write": enable_write,
            "write_function_code": write_function_code,
            "confirm_before_write": confirm_before_write,
            "write_rate_limit_ms": write_rate_limit_ms,
            "tag_mappings": tag_mappings,
        }

    if connector_type == "historian":
        historian_subtype = _normalize_historian_subtype(config.get("historian_subtype") or config.get("subtype"))
        retrieval_mode = _normalize_historian_retrieval_mode(config.get("retrieval_mode"))
        time_range_value = int(config.get("time_range_value") or 1)
        time_range_unit = _normalize_historian_time_range_unit(config.get("time_range_unit"))
        sampling_interval = _normalize_optional_text(config.get("sampling_interval"))
        max_data_points = int(config.get("max_data_points") or 500)
        authentication_mode = _normalize_historian_auth_mode(config.get("authentication_mode"))
        username = _normalize_optional_text(config.get("username"))
        if time_range_value < 1 or time_range_value > 10000:
            raise ValueError("config.time_range_value must be between 1 and 10000")
        if max_data_points < 1 or max_data_points > 5000:
            raise ValueError("config.max_data_points must be between 1 and 5000")
        normalized: dict[str, Any] = {
            "historian_subtype": historian_subtype,
            "retrieval_mode": retrieval_mode,
            "time_range_value": time_range_value,
            "time_range_unit": time_range_unit,
            "sampling_interval": sampling_interval,
            "cache_enabled": bool(config.get("cache_enabled")),
            "max_data_points": max_data_points,
            "authentication_mode": authentication_mode,
            "username": username,
        }
        if historian_subtype == "osisoft_pi":
            pi_server_url = _normalize_required_text(str(config.get("pi_server_url") or config.get("server_url") or ""), "config.pi_server_url")
            af_server = _normalize_required_text(str(config.get("af_server") or ""), "config.af_server")
            af_database = _normalize_required_text(str(config.get("af_database") or ""), "config.af_database")
            normalized.update(
                {
                    "pi_server_url": pi_server_url,
                    "af_server": af_server,
                    "af_database": af_database,
                    "tag_mappings": _normalize_historian_pi_tag_mappings(config.get("tag_mappings") or []),
                }
            )
            return normalized

        generic_mode = _normalize_historian_generic_mode(config.get("generic_mode"))
        timestamp_field = _normalize_required_text(str(config.get("timestamp_field") or ""), "config.timestamp_field")
        tag_field = _normalize_required_text(str(config.get("tag_field") or ""), "config.tag_field")
        value_field = _normalize_required_text(str(config.get("value_field") or ""), "config.value_field")
        normalized.update(
            {
                "generic_mode": generic_mode,
                "timestamp_field": timestamp_field,
                "tag_field": tag_field,
                "value_field": value_field,
            }
        )
        if generic_mode == "sql":
            db_type = _normalize_sql_db_type(config.get("db_type"))
            host = _normalize_required_text(str(config.get("host") or ""), "config.host")
            port = int(config.get("port") or (3306 if db_type == "mysql" else 1433 if db_type == "sqlserver" else 5432))
            database = _normalize_required_text(str(config.get("database") or ""), "config.database")
            username = _normalize_required_text(str(config.get("username") or ""), "config.username")
            query = _normalize_required_text(str(config.get("query") or ""), "config.query")
            if not re.match(r"^select\b", query, re.IGNORECASE):
                raise ValueError("config.query must start with SELECT")
            normalized.update(
                {
                    "db_type": db_type,
                    "host": host,
                    "port": port,
                    "database": database,
                    "username": username,
                    "ssl_enabled": bool(config.get("ssl_enabled")),
                    "query": query,
                }
            )
            return normalized

        endpoint_url = _normalize_required_text(str(config.get("endpoint_url") or ""), "config.endpoint_url")
        timeout_ms = int(config.get("timeout_ms") or 15000)
        if timeout_ms < 100 or timeout_ms > 60000:
            raise ValueError("config.timeout_ms must be between 100 and 60000")
        normalized.update(
            {
                "endpoint_url": endpoint_url,
                "array_path": _normalize_optional_text(config.get("array_path")),
                "timeout_ms": timeout_ms,
            }
        )
        return normalized

    db_type = _normalize_sql_db_type(config.get("db_type"))
    host = _normalize_required_text(str(config.get("host") or ""), "config.host")
    default_port = 3306 if db_type == "mysql" else 1433 if db_type == "sqlserver" else 5432
    port = int(config.get("port") or default_port)
    if port <= 0 or port > 65535:
        raise ValueError("config.port must be between 1 and 65535")
    database = _normalize_required_text(str(config.get("database") or ""), "config.database")
    username = _normalize_required_text(str(config.get("username") or ""), "config.username")
    pool_size = int(config.get("pool_size") or 5)
    if pool_size < 1 or pool_size > 50:
        raise ValueError("config.pool_size must be between 1 and 50")
    query_mode = _normalize_sql_query_mode(config.get("query_mode") or ("custom_query" if config.get("query") else "table"))
    refresh_mode = _normalize_sql_refresh_mode(config.get("refresh_mode"))
    table_schema = _normalize_optional_text(config.get("table_schema"))
    table_name = _normalize_optional_text(config.get("table_name"))
    custom_query = _normalize_optional_text(config.get("custom_query") or config.get("query"))
    if query_mode == "table" and not table_name:
        raise ValueError("config.table_name is required when query_mode is table")
    if query_mode == "custom_query":
        custom_query = _normalize_required_text(str(custom_query or ""), "config.custom_query")
        if not re.match(r"^select\b", custom_query, re.IGNORECASE):
            raise ValueError("config.custom_query must start with SELECT")
    tag_mappings = _normalize_sql_tag_mappings(config.get("tag_mappings"))
    tag_column = _normalize_optional_text(config.get("tag_column") or config.get("tagColumn"))
    value_column = _normalize_optional_text(config.get("value_column") or config.get("valueColumn"))
    if not tag_mappings and not (tag_column and value_column):
        raise ValueError("config.tag_mappings must include at least one source_column to target_tag mapping")
    return {
        "db_type": db_type,
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "ssl_enabled": bool(config.get("ssl_enabled")),
        "pool_size": pool_size,
        "query_mode": query_mode,
        "refresh_mode": refresh_mode,
        "table_schema": table_schema,
        "table_name": table_name,
        "custom_query": custom_query,
        "tag_column": tag_column,
        "value_column": value_column,
        "timestamp_column": _normalize_optional_text(config.get("timestamp_column")),
        "state_column": _normalize_optional_text(config.get("state_column")),
        "quality_column": _normalize_optional_text(config.get("quality_column")),
        "tag_mappings": tag_mappings,
    }


def _validate_plant_data_connector_secrets(
    connector_type: PlantGeniePlantDataConnectorType,
    secrets: dict[str, Any],
) -> dict[str, Any]:
    normalized = {str(key): value for key, value in secrets.items() if value is not None and str(key).strip()}
    if connector_type == "opcua":
        password = _normalize_optional_text(normalized.get("password"))
        trust_list_pems = _normalize_optional_string_list(normalized.get("trust_list_pems"), "secrets.trust_list_pems")
        client_certificate_pem = _normalize_optional_text(normalized.get("client_certificate_pem"))
        client_private_key_pem = _normalize_optional_text(normalized.get("client_private_key_pem"))
        client_private_key_password = _normalize_optional_text(normalized.get("client_private_key_password"))
        response: dict[str, Any] = {}
        if password:
            response["password"] = password
        if trust_list_pems:
            response["trust_list_pems"] = trust_list_pems
        if client_certificate_pem:
            response["client_certificate_pem"] = client_certificate_pem
        if client_private_key_pem:
            response["client_private_key_pem"] = client_private_key_pem
        if client_private_key_password:
            response["client_private_key_password"] = client_private_key_password
        return response

    if connector_type == "sql":
        connection_string = _normalize_optional_text(normalized.get("connection_string"))
        password = _normalize_optional_text(normalized.get("password"))
        if connection_string:
            return {"connection_string": connection_string}
        if password:
            return {"password": password}
        raise ValueError("secrets.password is required")

    if connector_type == "modbus_tcp":
        return {}

    if connector_type == "historian":
        authentication_mode = _normalize_historian_auth_mode(normalized.get("authentication_mode"))
        response: dict[str, Any] = {}
        password = _normalize_optional_text(normalized.get("password"))
        token = _normalize_optional_text(normalized.get("token"))
        if authentication_mode == "basic" and password:
            response["password"] = password
        if authentication_mode == "bearer" and token:
            response["token"] = token
        return response

    password = _normalize_optional_text(normalized.get("password"))
    certificate = _normalize_optional_text(normalized.get("ca_certificate_pem"))
    response: dict[str, Any] = {}
    if password:
        response["password"] = password
    if certificate:
        response["ca_certificate_pem"] = certificate
    return response