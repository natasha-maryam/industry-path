from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import cast, get_args
from urllib.parse import urlparse

from core.env_config import ensure_backend_env_loaded
from models.plant_genie import PlantGenieAIProvider, PlantGenieSupportedAIProvider
from services.plant_genie_config_errors import SecretConfigurationError


FRONTEND_SAFE_SECRET_STORAGE_MESSAGE = (
    "Backend configuration is incomplete. Please configure Plant Genie secret storage and restart the server."
)
DEFAULT_PLANT_GENIE_AI_PROVIDER: PlantGenieSupportedAIProvider = "openai"
SUPPORTED_PLANT_GENIE_AI_PROVIDERS = set(get_args(PlantGenieSupportedAIProvider))


@dataclass(frozen=True)
class PlantGenieSecretStorageValidationResult:
    env_path_loaded: str | None
    plant_genie_connector_secret_present: bool
    jwt_secret_present: bool
    postgres_password_present: bool
    database_url_present: bool
    database_url_password_present: bool
    database_url_password_matches_postgres_password: bool
    encryption_ready: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlantGenieAIProviderConfig:
    provider: PlantGenieSupportedAIProvider
    label: str
    endpoint_template: str
    adapter: str
    auth_scheme: str
    default_model: str | None = None


def validate_plant_genie_secret_storage() -> PlantGenieSecretStorageValidationResult:
    env_path = ensure_backend_env_loaded()

    plant_genie_connector_secret = os.getenv("PLANT_GENIE_CONNECTOR_SECRET", "").strip()
    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    postgres_password = os.getenv("POSTGRES_PASSWORD", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()

    parsed_password = ""
    database_url_password_present = False
    database_url_password_matches_postgres_password = True
    errors: list[str] = []
    warnings: list[str] = []

    if database_url:
        parsed = urlparse(database_url)
        parsed_password = parsed.password or ""
        database_url_password_present = bool(parsed_password)
        if not database_url_password_present:
            warnings.append("DATABASE_URL is set but does not include a password.")
        if postgres_password:
            database_url_password_matches_postgres_password = parsed_password == postgres_password
            if database_url_password_present and not database_url_password_matches_postgres_password:
                errors.append("DATABASE_URL password does not match POSTGRES_PASSWORD.")
        else:
            database_url_password_matches_postgres_password = not database_url_password_present
            if database_url_password_present:
                errors.append("POSTGRES_PASSWORD is missing while DATABASE_URL includes a password.")

    seed_present = bool(plant_genie_connector_secret or jwt_secret or postgres_password)
    if not seed_present:
        errors.append(
            "At least one secret seed must be configured: PLANT_GENIE_CONNECTOR_SECRET, JWT_SECRET, or POSTGRES_PASSWORD."
        )

    return PlantGenieSecretStorageValidationResult(
        env_path_loaded=str(env_path) if env_path is not None else None,
        plant_genie_connector_secret_present=bool(plant_genie_connector_secret),
        jwt_secret_present=bool(jwt_secret),
        postgres_password_present=bool(postgres_password),
        database_url_present=bool(database_url),
        database_url_password_present=database_url_password_present,
        database_url_password_matches_postgres_password=database_url_password_matches_postgres_password,
        encryption_ready=seed_present and not errors,
        errors=errors,
        warnings=warnings,
    )


def log_plant_genie_secret_storage_validation(
    result: PlantGenieSecretStorageValidationResult,
    *,
    logger: logging.Logger,
    context: str,
) -> None:
    logger.info(
        "Plant Genie secret storage validation [%s]: env_path=%s present={PLANT_GENIE_CONNECTOR_SECRET:%s, JWT_SECRET:%s, POSTGRES_PASSWORD:%s, DATABASE_URL:%s}",
        context,
        result.env_path_loaded or "not loaded",
        result.plant_genie_connector_secret_present,
        result.jwt_secret_present,
        result.postgres_password_present,
        result.database_url_present,
    )
    for warning in result.warnings:
        logger.warning("Plant Genie secret storage validation [%s] warning: %s", context, warning)
    for error in result.errors:
        logger.error("Plant Genie secret storage validation [%s] error: %s", context, error)


def ensure_plant_genie_secret_storage_ready(*, logger: logging.Logger, context: str) -> None:
    result = validate_plant_genie_secret_storage()
    log_plant_genie_secret_storage_validation(result, logger=logger, context=context)
    if not result.encryption_ready:
        raise SecretConfigurationError(FRONTEND_SAFE_SECRET_STORAGE_MESSAGE)


def resolve_default_plant_genie_ai_provider() -> PlantGenieSupportedAIProvider:
    ensure_backend_env_loaded()
    configured = (
        os.getenv("PLANT_GENIE_AI_PROVIDER", "").strip()
        or os.getenv("PLANT_GENIE_DEFAULT_PROVIDER", "").strip()
        or DEFAULT_PLANT_GENIE_AI_PROVIDER
    )
    normalized = configured.lower().replace("-", "_").replace(" ", "_")
    if normalized not in SUPPORTED_PLANT_GENIE_AI_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PLANT_GENIE_AI_PROVIDERS))
        raise ValueError(
            f"Unsupported Plant Genie AI provider '{configured}'. Supported providers: {supported}."
        )
    return cast(PlantGenieSupportedAIProvider, normalized)


def _normalize_provider_endpoint(value: str, *, config_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{config_name} is not configured on the server.")

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{config_name} must be a valid http or https URL.")
    return normalized


def resolve_plant_genie_ai_provider_config(provider: PlantGenieAIProvider) -> PlantGenieAIProviderConfig:
    ensure_backend_env_loaded()
    default_model = os.getenv("PLANT_GENIE_DEFAULT_MODEL", "").strip() or None

    if provider == "openai":
        return PlantGenieAIProviderConfig(
            provider="openai",
            label="OpenAI",
            endpoint_template="https://api.openai.com/v1/chat/completions",
            adapter="openai_chat_completions",
            auth_scheme="bearer",
            default_model=os.getenv("PLANT_GENIE_OPENAI_MODEL", "").strip() or default_model,
        )

    if provider == "anthropic":
        return PlantGenieAIProviderConfig(
            provider="anthropic",
            label="Anthropic",
            endpoint_template="https://api.anthropic.com/v1/messages",
            adapter="anthropic_messages",
            auth_scheme="anthropic",
            default_model=os.getenv("PLANT_GENIE_ANTHROPIC_MODEL", "").strip() or default_model,
        )

    if provider == "azure_openai":
        return PlantGenieAIProviderConfig(
            provider="azure_openai",
            label="Azure OpenAI",
            endpoint_template=_normalize_provider_endpoint(
                os.getenv("PLANT_GENIE_AZURE_OPENAI_ENDPOINT", ""),
                config_name="PLANT_GENIE_AZURE_OPENAI_ENDPOINT",
            ),
            adapter="openai_chat_completions",
            auth_scheme="azure_api_key",
            default_model=os.getenv("PLANT_GENIE_AZURE_OPENAI_MODEL", "").strip() or default_model,
        )

    if provider == "openrouter":
        return PlantGenieAIProviderConfig(
            provider="openrouter",
            label="OpenRouter",
            endpoint_template="https://openrouter.ai/api/v1/chat/completions",
            adapter="openai_chat_completions",
            auth_scheme="bearer",
            default_model=os.getenv("PLANT_GENIE_OPENROUTER_MODEL", "").strip() or default_model,
        )

    supported = ", ".join(("openai", "anthropic", "azure_openai", "openrouter"))
    raise ValueError(f"Unsupported Plant Genie AI provider '{provider}'. Supported providers: {supported}.")


def build_plant_genie_provider_endpoint(config: PlantGenieAIProviderConfig, *, model: str | None = None) -> str:
    endpoint = config.endpoint_template
    if "{deployment}" not in endpoint:
        return endpoint

    deployment = str(model or "").strip()
    if not deployment:
        raise ValueError(
            f"{config.label} requires a model because the configured endpoint template uses {{deployment}}."
        )
    return endpoint.replace("{deployment}", deployment)