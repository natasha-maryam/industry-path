from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException

from core.database import redis_store


def _limit_requests_per_minute() -> int:
    try:
        value = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MIN", "120"))
        return max(1, value)
    except Exception:
        return 120


def enforce_rate_limit(user_id: str, route_scope: str = "global") -> dict[str, Any]:
    limit = _limit_requests_per_minute()
    bucket_key = f"rate:{route_scope}:{user_id}"
    count = redis_store.incr_with_window(bucket_key, window_seconds=60)
    if count > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return {
        "count": count,
        "limit": limit,
        "window_seconds": 60,
    }
