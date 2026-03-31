from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Callable, Mapping

from models.copilot import CopilotRunResponse


ProviderHandler = Callable[[str, Mapping[str, Any]], dict[str, Any]]


@dataclass
class AIProvider:
    name: str
    handler: ProviderHandler
    system_prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProviderManager:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register_provider(
        self,
        name: str,
        handler: ProviderHandler | None = None,
        system_prompt: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider_name = str(name or "").strip().lower()
        if not provider_name:
            raise ValueError("provider name is required")

        self._providers[provider_name] = AIProvider(
            name=provider_name,
            handler=handler or self._missing_handler,
            system_prompt=system_prompt,
            metadata=dict(metadata or {}),
        )
        return {
            "provider": provider_name,
            "registered": True,
            "metadata": dict(metadata or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, provider: str, prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        provider_name = str(provider or "openai").strip().lower() or "openai"
        selected = self._providers.get(provider_name)
        if selected is None:
            raise ValueError("Connect AI to use Automation Copilot.")

        output = dict(selected.handler(prompt, context))
        output.setdefault("provider", provider_name)
        output.setdefault("metadata", selected.metadata)
        output.setdefault("system_prompt", selected.system_prompt)
        return output

    @staticmethod
    def _missing_handler(prompt: str, context: Mapping[str, Any]) -> dict[str, Any]:
        _ = prompt
        _ = context
        raise ValueError("Connect AI to use Automation Copilot.")


def build_prompt(task: str, context: Mapping[str, Any]) -> str:
    normalized_task = str(task or "").strip()
    context_blob = json.dumps(dict(context), indent=2, sort_keys=True, default=str)
    return f"Task: {normalized_task}\n\nContext:\n{context_blob}"


class CopilotEngine:
    def __init__(self) -> None:
        self.providers = AIProviderManager()

    def register_provider(
        self,
        name: str,
        system_prompt: str | None = None,
        mock_response: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        _ = mock_response
        payload = dict(metadata or {})
        return self.providers.register_provider(name, system_prompt=system_prompt, metadata=payload)

    def run(self, command: str, provider: str = "openai", context: Mapping[str, Any] | None = None) -> CopilotRunResponse:
        normalized_command = str(command or "").strip()
        if not normalized_command:
            raise ValueError("command is required")

        runtime_context = dict(context or {})
        prompt = build_prompt(normalized_command, runtime_context)
        provider_output = self.providers.execute(provider, prompt, runtime_context)
        return CopilotRunResponse(
            command=normalized_command,
            provider=provider,
            mode="ai_fallback",
            prompt=prompt,
            warnings=[],
            result=provider_output,
        )


copilot_engine = CopilotEngine()