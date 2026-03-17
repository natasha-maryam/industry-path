from __future__ import annotations

from threading import Lock
from typing import Any


class RuntimeTelemetry:
    """In-memory runtime tag cache used by API and WebSocket streaming."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._tags: dict[str, Any] = {}

    def update_tag(self, name: str, value: Any) -> None:
        with self._lock:
            self._tags[name] = value

    def update_tags(self, values: dict[str, Any]) -> None:
        with self._lock:
            self._tags.update(values)

    def get_all_tags(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._tags)

    def clear(self) -> None:
        with self._lock:
            self._tags.clear()


runtime_telemetry = RuntimeTelemetry()
