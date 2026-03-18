from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel

from runtime_engine.runtime_manager import runtime_manager
from runtime_engine.runtime_evaluator import runtime_evaluator
from runtime_engine.runtime_signal_state import runtime_signal_state
from runtime_engine.runtime_state_server import runtime_stream
from runtime_engine.runtime_telemetry import runtime_telemetry
from services.simulation_service import simulation_service

router = APIRouter(prefix="/runtime", tags=["runtime"])


class RuntimeDeployRequest(BaseModel):
    project_id: str


class RuntimeForceInputRequest(BaseModel):
    tag: str
    value: Any
    type: str | None = None


class RuntimeClearForceRequest(BaseModel):
    tag: str


class RuntimeRunEvaluationRequest(BaseModel):
    reason: str = "manual_debug"


def _runtime_project_guard(project_id: str) -> None:
    status = runtime_manager.status()
    active_project_id = status.get("project_id")
    if active_project_id and active_project_id != project_id:
        raise HTTPException(
            status_code=409,
            detail=f"Runtime is active for project `{active_project_id}` not `{project_id}`.",
        )


@router.post("/deploy")
def deploy_runtime(payload: RuntimeDeployRequest) -> dict[str, Any]:
    return runtime_manager.deploy(payload.project_id)


@router.post("/start")
def start_runtime() -> dict[str, Any]:
    return runtime_manager.start()


@router.post("/stop")
def stop_runtime() -> dict[str, Any]:
    return runtime_manager.stop()


@router.post("/restart")
def restart_runtime() -> dict[str, Any]:
    return runtime_manager.restart()


@router.get("/tags")
def get_runtime_tags() -> dict[str, Any]:
    return runtime_telemetry.get_all_tags()


@router.post("/{project_id}/force-input")
def force_runtime_input(project_id: str, payload: RuntimeForceInputRequest) -> dict[str, Any]:
    _runtime_project_guard(project_id)
    baseline = runtime_signal_state.get_project_snapshot(project_id).get("current_values", {})
    try:
        forced_state = runtime_signal_state.apply_force(
            project_id=project_id,
            tag=payload.tag,
            value=payload.value,
            declared_type=payload.type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cycle = runtime_evaluator.run_cycle(
        project_id,
        reason="force_input",
        forced_tag=payload.tag,
        forced_value=payload.value,
        baseline_values=dict(baseline),
    )
    trace = simulation_service.capture_trace(project_id, reset=False, step_ms=100, duration_ms=1000)

    return {
        "success": True,
        "message": f"Applied force for `{payload.tag}`.",
        "project_id": project_id,
        "forced": forced_state,
        "changed_signals": cycle.get("changed_signals", []),
        "changed_alarms": cycle.get("changed_alarms", []),
        "changed_health_checks": cycle.get("changed_health_checks", []),
        "evaluation_cycle": cycle,
        "trace_samples": len(trace),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{project_id}/clear-force")
def clear_runtime_force(project_id: str, payload: RuntimeClearForceRequest) -> dict[str, Any]:
    _runtime_project_guard(project_id)
    baseline = runtime_signal_state.get_project_snapshot(project_id).get("current_values", {})
    try:
        cleared_state = runtime_signal_state.clear_force(project_id=project_id, tag=payload.tag)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cycle = runtime_evaluator.run_cycle(
        project_id,
        reason="clear_force",
        forced_tag=payload.tag,
        forced_value=None,
        baseline_values=dict(baseline),
    )
    trace = simulation_service.capture_trace(project_id, reset=False, step_ms=100, duration_ms=800)

    return {
        "success": True,
        "message": f"Cleared force for `{payload.tag}`.",
        "project_id": project_id,
        "forced": cleared_state,
        "changed_signals": cycle.get("changed_signals", []),
        "changed_alarms": cycle.get("changed_alarms", []),
        "changed_health_checks": cycle.get("changed_health_checks", []),
        "evaluation_cycle": cycle,
        "trace_samples": len(trace),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{project_id}/forced-inputs")
def get_forced_runtime_inputs(project_id: str) -> dict[str, Any]:
    forced_inputs = runtime_signal_state.get_forced_inputs(project_id)
    input_catalog = runtime_signal_state.get_input_catalog(project_id)
    diagnostics = runtime_evaluator.get_last_cycle(project_id)
    return {
        "success": True,
        "message": "Forced input state fetched.",
        "project_id": project_id,
        "forced_inputs": forced_inputs,
        "input_catalog": input_catalog,
        "diagnostics": diagnostics,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{project_id}/run-evaluation-cycle")
def run_runtime_evaluation_cycle(project_id: str, payload: RuntimeRunEvaluationRequest) -> dict[str, Any]:
    _runtime_project_guard(project_id)
    cycle = runtime_evaluator.run_cycle(project_id, reason=payload.reason)
    trace = simulation_service.capture_trace(project_id, reset=False, step_ms=100, duration_ms=1200)
    return {
        "success": True,
        "message": "Evaluation cycle completed.",
        "project_id": project_id,
        "changed_signals": cycle.get("changed_signals", []),
        "changed_alarms": cycle.get("changed_alarms", []),
        "changed_health_checks": cycle.get("changed_health_checks", []),
        "evaluation_cycle": cycle,
        "trace_samples": len(trace),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{project_id}/diagnostics")
def get_runtime_diagnostics(project_id: str) -> dict[str, Any]:
    _runtime_project_guard(project_id)
    cycle = runtime_evaluator.get_last_cycle(project_id)
    return {
        "success": True,
        "project_id": project_id,
        "diagnostics": cycle,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.websocket("/stream")
async def runtime_tag_stream(websocket: WebSocket) -> None:
    await runtime_stream(websocket)
