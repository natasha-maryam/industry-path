from __future__ import annotations

import time
from collections import defaultdict
from threading import RLock
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestMetricsStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._totals = defaultdict(int)
        self._errors = defaultdict(int)
        self._durations_ms: dict[str, float] = defaultdict(float)

    def record(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        key = f"{method} {path}"
        with self._lock:
            self._totals[key] += 1
            self._durations_ms[key] += duration_ms
            if status_code >= 400:
                self._errors[key] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            rows = []
            for key in sorted(self._totals.keys()):
                total = self._totals[key]
                duration_total = self._durations_ms.get(key, 0.0)
                rows.append(
                    {
                        "route": key,
                        "count": total,
                        "errors": self._errors.get(key, 0),
                        "avg_duration_ms": round(duration_total / max(1, total), 3),
                    }
                )
            return {
                "routes": rows,
            }


request_metrics_store = RequestMetricsStore()


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        request_metrics_store.record(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-Duration-Ms"] = f"{duration_ms:.2f}"
        return response
