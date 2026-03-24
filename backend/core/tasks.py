from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from services.behavior_loader_patch import behavior_loader_patch
from services.uns_core import uns_core

try:
    from celery import Celery  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Celery = None


def _broker_url() -> str:
    return os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))


def _result_backend() -> str:
    return os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))


celery_app = Celery("crosslayerx") if Celery is not None else None
if celery_app is not None:
    celery_app.conf.broker_url = _broker_url()
    celery_app.conf.result_backend = _result_backend()


if celery_app is not None:

    @celery_app.task(name="production.runtime_update")
    def runtime_update_task(project_id: str, updates: dict[str, dict[str, Any]]) -> dict[str, Any]:
        uns_result = uns_core.update_runtime(updates)
        behavior_result = behavior_loader_patch.push_runtime_updates(project_id, updates)
        return {
            "uns": uns_result,
            "behavior": behavior_result,
        }

    @celery_app.task(name="production.run_script")
    def run_script_task(script: str) -> dict[str, Any]:
        return uns_core.run_script(script)


def enqueue_runtime_update(project_id: str, updates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if celery_app is None:
        return {
            "task_id": f"inline-{uuid4()}",
            "queued": False,
            "result": {
                "uns": uns_core.update_runtime(updates),
                "behavior": behavior_loader_patch.push_runtime_updates(project_id, updates),
            },
        }

    async_result = celery_app.send_task("production.runtime_update", args=[project_id, updates])
    return {
        "task_id": async_result.id,
        "queued": True,
    }


def enqueue_script(script: str) -> dict[str, Any]:
    if celery_app is None:
        return {
            "task_id": f"inline-{uuid4()}",
            "queued": False,
            "result": uns_core.run_script(script),
        }

    async_result = celery_app.send_task("production.run_script", args=[script])
    return {
        "task_id": async_result.id,
        "queued": True,
    }
