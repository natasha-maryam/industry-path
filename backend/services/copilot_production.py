from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from threading import Lock
from time import monotonic
from typing import Any, Callable, Mapping
from uuid import uuid4

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from models.copilot import CopilotProductionResult


ProviderHandler = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]
_ALLOWED_CONTEXT_KEYS = frozenset({"request_id", "session_id", "source"})


class ProviderNotConfiguredError(ValueError):
    pass


@dataclass
class AIProvider:
    name: str
    handler: ProviderHandler
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    payload: dict[str, Any]
    expires_at: float
    created_at: float


class TTLResponseCache:
    def __init__(self, ttl_seconds: int = 300, max_entries: int = 256) -> None:
        self._ttl_seconds = max(1, int(ttl_seconds))
        self._max_entries = max(1, int(max_entries))
        self._entries: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        now = monotonic()
        with self._lock:
            self._prune_locked(now)
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._entries.pop(key, None)
                return None
            return deepcopy(entry.payload)

    def set(self, key: str, payload: Mapping[str, Any]) -> None:
        now = monotonic()
        with self._lock:
            self._prune_locked(now)
            self._entries[key] = CacheEntry(
                payload=deepcopy(dict(payload)),
                expires_at=now + self._ttl_seconds,
                created_at=now,
            )
            if len(self._entries) > self._max_entries:
                oldest_key = min(self._entries.items(), key=lambda item: item[1].created_at)[0]
                self._entries.pop(oldest_key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _prune_locked(self, now: float) -> None:
        expired = [key for key, entry in self._entries.items() if entry.expires_at <= now]
        for key in expired:
            self._entries.pop(key, None)


class AIProviderManager:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._cache = TTLResponseCache(ttl_seconds=300, max_entries=256)

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
            handler=handler or self._unconfigured_handler,
            metadata=dict(metadata or {}),
        )
        self._cache.clear()
        return {
            "connector": provider_name,
            "registered": True,
            "metadata": dict(metadata or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, provider: str, prompt: str, context: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        provider_name = _normalize_connector_name(provider)
        selected = self._providers.get(provider_name)
        if selected is None:
            raise ProviderNotConfiguredError(f"Plant Genie connector '{provider_name}' is not configured.")

        cache_key = self._build_cache_key(provider_name, prompt, context)
        cached_payload = self._cache.get(cache_key)
        if cached_payload is not None:
            cached_payload.setdefault("connector", provider_name)
            cached_payload.setdefault("metadata", selected.metadata)
            return cached_payload, True

        payload = _execute_provider_handler(selected.handler, prompt, dict(context))
        output = dict(payload)
        output.setdefault("connector", provider_name)
        output.setdefault("metadata", selected.metadata)
        self._cache.set(cache_key, output)
        return output, False

    @staticmethod
    def _build_cache_key(provider: str, prompt: str, context: Mapping[str, Any]) -> str:
        context_blob = json.dumps(dict(context), sort_keys=True, default=str)
        return sha256(f"{provider}\n{prompt}\n{context_blob}".encode("utf-8")).hexdigest()

    @staticmethod
    def _unconfigured_handler(prompt: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
        _ = prompt
        _ = context
        # TODO: bridge registered Plant Genie connectors to user-managed AI runtimes.
        raise ProviderNotConfiguredError("Plant Genie connector is registered but no execution adapter is available.")


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.2, min=0.2, max=1.0),
    retry=retry_if_exception_type(Exception),
)
def _execute_provider_handler(handler: ProviderHandler, prompt: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
    return handler(prompt, context)


def _normalize_connector_name(connector: str) -> str:
    normalized = str(connector or "").strip().lower()
    if not normalized:
        raise ValueError("connector is required")
    return normalized


def _dev_mock_enabled() -> bool:
    return os.getenv("PLANT_GENIE_ENABLE_DEV_MOCK", "false").strip().lower() in {"1", "true", "yes", "on"}


def _build_mock_handler(mock_response: str) -> ProviderHandler:
    response_text = str(mock_response or "").strip() or "DEV MOCK: Plant Genie connector responded without live execution."

    def handler(command: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
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

    # TODO: allow connector-specific grounding only after access-control policy is defined.
    return allowed, dropped


@dataclass
class JobRecord:
    job_id: str
    status: str
    submitted_at: str
    command: str | None = None
    provider: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "success": self.status != "failed",
            "job_id": self.job_id,
            "status": self.status,
            "command": self.command,
            "provider": self.provider,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "error_code": self.error_code,
            "result": deepcopy(self.result),
        }


_job_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="copilot-production")
_job_lock = Lock()
_jobs: dict[str, JobRecord] = {}


def run_job(fn: Callable[..., dict[str, Any]], *args: Any) -> dict[str, Any]:
    job_id = f"copilot-job-{uuid4()}"
    submitted_at = datetime.now(timezone.utc).isoformat()
    command = str(args[0]) if len(args) > 0 and isinstance(args[0], str) else None
    connector = str(args[1]) if len(args) > 1 and isinstance(args[1], str) else None
    with _job_lock:
        _jobs[job_id] = JobRecord(
            job_id=job_id,
            status="queued",
            submitted_at=submitted_at,
            command=command,
            provider=connector,
        )

    def runner() -> None:
        with _job_lock:
            record = _jobs[job_id]
            record.status = "running"
            record.started_at = datetime.now(timezone.utc).isoformat()
        try:
            result = fn(*args)
            with _job_lock:
                record = _jobs[job_id]
                record.status = "completed"
                record.completed_at = datetime.now(timezone.utc).isoformat()
                record.result = deepcopy(result)
        except Exception as exc:
            with _job_lock:
                record = _jobs[job_id]
                record.status = "failed"
                record.completed_at = datetime.now(timezone.utc).isoformat()
                record.error = str(exc)
                record.error_code = _classify_error(exc)

    _job_executor.submit(runner)
    return _jobs[job_id].as_dict()


def get_job(job_id: str) -> dict[str, Any]:
    with _job_lock:
        record = _jobs.get(job_id)
        if record is None:
            raise KeyError(job_id)
        return record.as_dict()


def _classify_error(exc: Exception) -> str:
    if isinstance(exc, ProviderNotConfiguredError):
        return "connector_not_configured"
    if isinstance(exc, ValueError):
        return "invalid_request"
    return "processing_failed"


class CopilotProduction:
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

    def run(
        self,
        command: str,
        connector: str,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_command = str(command or "").strip()
        if not normalized_command:
            raise ValueError("command is required")

        connector_name = _normalize_connector_name(connector)
        runtime_context, dropped = sanitize_connector_context(context)
        provider_output, cached = self.providers.execute(connector_name, normalized_command, runtime_context)
        warnings: list[str] = []
        if dropped:
            warnings.append(
                "Plant Genie ignored local workspace context. Connector grounding remains disabled until an explicit policy is implemented."
            )
        summary = str(provider_output.get("message") or "Connector response received.")
        return self._wrap_result(
            result_type="connector",
            connector=connector_name,
            summary=summary,
            data=dict(provider_output),
            warnings=warnings,
            request=normalized_command,
            cached=cached,
        )

    @staticmethod
    def _wrap_result(
        result_type: str,
        connector: str,
        summary: str,
        data: Mapping[str, Any],
        warnings: list[str] | None = None,
        request: str | None = None,
        cached: bool = False,
    ) -> dict[str, Any]:
        payload = CopilotProductionResult(
            type=result_type,
            summary=summary,
            warnings=list(warnings or []),
            request=request,
            cached=cached,
            connector=connector,
            data=dict(data),
        )
        return payload.model_dump()


copilot_production = CopilotProduction()