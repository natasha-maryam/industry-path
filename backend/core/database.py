from __future__ import annotations

import json
import os
from threading import RLock
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None


class RedisStore:
    """Redis-backed helper with in-memory fallback for local/dev compatibility."""

    def __init__(self) -> None:
        self._memory_lock = RLock()
        self._memory: dict[str, Any] = {}
        self._redis = self._build_redis_client()

    @staticmethod
    def _redis_url() -> str:
        return os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    def _build_redis_client(self):
        if redis is None:
            return None
        try:
            client = redis.from_url(self._redis_url(), decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    @property
    def is_redis_enabled(self) -> bool:
        return self._redis is not None

    def set_json(self, key: str, payload: Any, ttl_seconds: int | None = None) -> None:
        serialized = json.dumps(payload, default=str)
        if self._redis is not None:
            self._redis.set(key, serialized, ex=ttl_seconds)
            return
        with self._memory_lock:
            self._memory[key] = payload

    def get_json(self, key: str, default: Any = None) -> Any:
        if self._redis is not None:
            raw = self._redis.get(key)
            if raw is None:
                return default
            try:
                return json.loads(raw)
            except Exception:
                return default

        with self._memory_lock:
            return self._memory.get(key, default)

    def append_json_list(self, key: str, payload: Any, max_items: int = 1000) -> None:
        if self._redis is not None:
            pipeline = self._redis.pipeline()
            pipeline.lpush(key, json.dumps(payload, default=str))
            pipeline.ltrim(key, 0, max_items - 1)
            pipeline.execute()
            return

        with self._memory_lock:
            current = self._memory.get(key)
            if not isinstance(current, list):
                current = []
            current.insert(0, payload)
            self._memory[key] = current[:max_items]

    def get_json_list(self, key: str, limit: int = 100) -> list[Any]:
        if self._redis is not None:
            raw_items = self._redis.lrange(key, 0, max(0, limit - 1))
            output: list[Any] = []
            for item in raw_items:
                try:
                    output.append(json.loads(item))
                except Exception:
                    continue
            return output

        with self._memory_lock:
            current = self._memory.get(key)
            if not isinstance(current, list):
                return []
            return list(current[:limit])

    def incr_with_window(self, key: str, window_seconds: int) -> int:
        if self._redis is not None:
            pipeline = self._redis.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, max(1, window_seconds))
            result = pipeline.execute()
            return int(result[0])

        with self._memory_lock:
            current = int(self._memory.get(key, 0)) + 1
            self._memory[key] = current
            return current


redis_store = RedisStore()
