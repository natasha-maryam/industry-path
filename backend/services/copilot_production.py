from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from threading import Lock
from time import monotonic
from typing import Any, Callable, Mapping
from uuid import uuid4

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from models.copilot import CopilotProductionResult
from services.deterministic_behavior_service import deterministic_behavior_service


ProviderHandler = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


class ProviderNotConfiguredError(ValueError):
    pass


@dataclass
class AIProvider:
    name: str
    handler: ProviderHandler
    system_prompt: str | None = None
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
        system_prompt: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider_name = str(name or "").strip().lower()
        if not provider_name:
            raise ValueError("provider name is required")

        self._providers[provider_name] = AIProvider(
            name=provider_name,
            handler=handler or self._unconfigured_handler,
            system_prompt=system_prompt,
            metadata=dict(metadata or {}),
        )
        self._cache.clear()
        return {
            "provider": provider_name,
            "registered": True,
            "metadata": dict(metadata or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, provider: str, prompt: str, context: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        provider_name = str(provider or "openai").strip().lower() or "openai"
        selected = self._providers.get(provider_name)
        if selected is None:
            raise ProviderNotConfiguredError(f"Provider '{provider_name}' is not configured.")

        cache_key = self._build_cache_key(provider_name, prompt, context)
        cached_payload = self._cache.get(cache_key)
        if cached_payload is not None:
            cached_payload.setdefault("provider", provider_name)
            cached_payload.setdefault("metadata", selected.metadata)
            cached_payload.setdefault("system_prompt", selected.system_prompt)
            return cached_payload, True

        payload = _execute_provider_handler(selected.handler, prompt, dict(context))
        output = dict(payload)
        output.setdefault("provider", provider_name)
        output.setdefault("metadata", selected.metadata)
        output.setdefault("system_prompt", selected.system_prompt)
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
        raise ProviderNotConfiguredError("Connect AI to use Automation Copilot.")


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.2, min=0.2, max=1.0),
    retry=retry_if_exception_type(Exception),
)
def _execute_provider_handler(handler: ProviderHandler, prompt: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
    return handler(prompt, context)


def enforce_prompt(task: str, rows: list[Mapping[str, Any]]) -> str:
    normalized_task = str(task or "").strip()
    row_preview = [
        {
            "tag": row.get("tag"),
            "type": row.get("type"),
            "system": row.get("system"),
            "equipment": row.get("equipment"),
            "state": row.get("state"),
            "mode": row.get("mode"),
            "warnings": row.get("warnings", []),
            "upstream": row.get("upstream", [])[:4],
            "downstream": row.get("downstream", [])[:4],
        }
        for row in rows[:8]
    ]
    context_blob = json.dumps(row_preview, indent=2, sort_keys=True, default=str)
    return (
        "You are the production automation copilot. "
        "Stay grounded in deterministic plant context, avoid fabricating topology, and prefer concise operational guidance.\n\n"
        f"Task: {normalized_task}\n\n"
        "Relevant engineering rows:\n"
        f"{context_blob}"
    )


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
    provider = str(args[1]) if len(args) > 1 and isinstance(args[1], str) else None
    with _job_lock:
        _jobs[job_id] = JobRecord(
            job_id=job_id,
            status="queued",
            submitted_at=submitted_at,
            command=command,
            provider=provider,
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
        return "provider_not_configured"
    if isinstance(exc, ValueError):
        return "invalid_request"
    return "processing_failed"


class CopilotProduction:
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

    def run(
        self,
        command: str,
        provider: str = "openai",
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_command = str(command or "").strip()
        if not normalized_command:
            raise ValueError("command is required")

        runtime_context = dict(context or {})
        prompt_rows = self._prompt_rows(runtime_context)
        prompt = enforce_prompt(normalized_command, prompt_rows)
        provider_output, cached = self.providers.execute(provider, prompt, runtime_context)
        summary = str(provider_output.get("message") or "AI response generated.")
        return self._wrap_result(
            result_type="ai",
            provider=provider,
            summary=summary,
            data=dict(provider_output),
            prompt=prompt,
            cached=cached,
        )

    def _prompt_rows(self, context: Mapping[str, Any]) -> list[dict[str, Any]]:
        selected_row = context.get("engineering_table", {}).get("selected_row") if isinstance(context.get("engineering_table"), Mapping) else None
        rows: list[dict[str, Any]] = []
        if isinstance(selected_row, Mapping):
            rows.append(dict(selected_row))

        selected_tag = self._context_selected_tag(context)
        resolved_tag = deterministic_behavior_service.resolve_row_tag(selected_tag) if selected_tag else None
        if resolved_tag:
            row = deterministic_behavior_service.get_row(resolved_tag)
            if row is not None:
                rows.append(row.as_dict())

        sample_tags = []
        engineering_table = context.get("engineering_table")
        if isinstance(engineering_table, Mapping):
            raw_sample_tags = engineering_table.get("sample_tags")
            if isinstance(raw_sample_tags, list):
                sample_tags = [str(item) for item in raw_sample_tags[:6] if item]

        for raw_tag in sample_tags:
            resolved_sample = deterministic_behavior_service.resolve_row_tag(raw_tag) or raw_tag
            row = deterministic_behavior_service.get_row(resolved_sample)
            if row is not None:
                rows.append(row.as_dict())

        unique_rows: list[dict[str, Any]] = []
        seen_tags: set[str] = set()
        for row in rows:
            tag = str(row.get("tag") or "").strip()
            if not tag or tag in seen_tags:
                continue
            seen_tags.add(tag)
            unique_rows.append(row)
        return unique_rows

    @staticmethod
    def _context_selected_tag(context: Mapping[str, Any]) -> str | None:
        value = context.get("selected_tag")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _wrap_result(
        result_type: str,
        provider: str,
        summary: str,
        data: Mapping[str, Any],
        warnings: list[str] | None = None,
        prompt: str | None = None,
        cached: bool = False,
    ) -> dict[str, Any]:
        payload = CopilotProductionResult(
            type=result_type,
            summary=summary,
            warnings=list(warnings or []),
            prompt=prompt,
            cached=cached,
            provider=provider,
            data=dict(data),
        )
        return payload.model_dump()


copilot_production = CopilotProduction()