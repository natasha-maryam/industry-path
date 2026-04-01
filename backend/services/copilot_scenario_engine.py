from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Any, Callable, Mapping

from models.copilot import CopilotRunResponse


ProviderHandler = Callable[[str, Mapping[str, Any]], dict[str, Any]]
_ALLOWED_CONTEXT_KEYS = frozenset({"request_id", "session_id", "source"})


@dataclass
class AIProvider:
    name: str
    handler: ProviderHandler
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProviderManager:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register_provider(
        self,
        name: str,
        handler: ProviderHandler | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider_name = str(name or "").strip().lower()
        if not provider_name:
            raise ValueError("provider name is required")

        self._providers[provider_name] = AIProvider(
            name=provider_name,
            handler=handler or self._missing_handler,
            metadata=dict(metadata or {}),
        )
        return {
            "connector": provider_name,
            "registered": True,
            "metadata": dict(metadata or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, provider: str, prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        provider_name = _normalize_connector_name(provider)
        selected = self._providers.get(provider_name)
        if selected is None:
            raise ValueError(f"Plant Genie connector '{provider_name}' is not configured.")

        output = dict(selected.handler(prompt, context))
        output.setdefault("connector", provider_name)
        output.setdefault("metadata", selected.metadata)
        return output

    @staticmethod
    def _missing_handler(prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        _ = prompt
        _ = context
        # TODO: forward command-only requests to a user-managed AI connector adapter.
        raise ValueError("Plant Genie connector is registered but no execution adapter is available.")


def _normalize_connector_name(connector: str) -> str:
    normalized = str(connector or "").strip().lower()
    if not normalized:
        raise ValueError("connector is required")
    return normalized


def _dev_mock_enabled() -> bool:
    return os.getenv("PLANT_GENIE_ENABLE_DEV_MOCK", "false").strip().lower() in {"1", "true", "yes", "on"}


def _build_mock_handler(mock_response: str) -> ProviderHandler:
    response_text = str(mock_response or "").strip() or "DEV MOCK: Plant Genie connector responded without live execution."

    def handler(command: str, context: Mapping[str, Any]) -> dict[str, Any]:
        _ = command
        _ = context
        return {
            "message": response_text,
            "mock": True,
        }

    return handler


def sanitize_connector_context(context: Mapping[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    runtime_context = dict(context or {})
    allowed: dict[str, Any] = {}
    dropped: list[str] = []
    for key, value in runtime_context.items():
        if key in _ALLOWED_CONTEXT_KEYS:
            allowed[key] = value
            continue
        dropped.append(str(key))

    # TODO: allow connector-specific context fields only after a grounding policy is defined.
    return allowed, dropped


class CopilotEngine:
    def __init__(self) -> None:
        self.providers = AIProviderManager()

    def register_provider(
        self,
        name: str,
        mock_response: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = dict(metadata or {})
        handler = None
        if mock_response is not None:
            if not _dev_mock_enabled():
                raise ValueError("Mock connectors are disabled. Set PLANT_GENIE_ENABLE_DEV_MOCK=true to enable them.")
            handler = _build_mock_handler(mock_response)
            payload["mock"] = True

        return self.providers.register_provider(name, handler=handler, metadata=payload)

    def run(self, command: str, connector: str, context: Mapping[str, Any] | None = None) -> CopilotRunResponse:
        normalized_command = str(command or "").strip()
        if not normalized_command:
            raise ValueError("command is required")

        connector_name = _normalize_connector_name(connector)
        runtime_context, dropped = sanitize_connector_context(context)
        provider_output = self.providers.execute(connector_name, normalized_command, runtime_context)
        warnings: list[str] = []
        if dropped:
            warnings.append(
                "Plant Genie ignored local workspace context. Connector grounding remains disabled until an explicit policy is implemented."
            )
        return CopilotRunResponse(
            command=normalized_command,
            connector=connector_name,
            mode="connector_gateway",
            request=normalized_command,
            warnings=warnings,
            result=provider_output,
        )


copilot_engine = CopilotEngine()