from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, WebSocket
from pydantic import BaseModel

from models.runtime_deployment import RuntimeStateResponse
from runtime_engine.runtime_manager import runtime_manager
from runtime_engine.runtime_evaluator import runtime_evaluator
from runtime_engine.runtime_signal_state import runtime_signal_state
from runtime_engine.runtime_state_server import runtime_stream
from runtime_engine.runtime_telemetry import runtime_telemetry
from services.project_service import project_service
from services.runtime_deployment_store import runtime_deployment_store
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
    project_service.ensure_project(payload.project_id)
    result = runtime_manager.deploy(payload.project_id)
    runtime_deployment_store.upsert_project_deployment(
        project_id=payload.project_id,
        target_runtime=str(result.get("target_runtime") or "headless-matiec"),
        protocol=str(result.get("protocol") or "BEREMIZ"),
        plc_address=result.get("plc_address"),
        io_config_json=result.get("io_rows") or [],
        deploy_status="deployed" if result.get("status") == "passed" else "failed",
        validation_status=str(result.get("status") or "failed"),
        deployed_version=result.get("deployed_version"),
        artifact_path=result.get("artifact_path"),
        last_error="\n".join(result.get("errors", [])) if result.get("errors") else None,
    )
    return result


@router.post("/start")
def start_runtime() -> dict[str, Any]:
    result = runtime_manager.start()
    status = runtime_manager.status()
    project_id = status.get("project_id")
    if project_id:
        current = runtime_deployment_store.get_latest(project_id)
        if current:
            runtime_deployment_store.upsert_project_deployment(
                project_id=project_id,
                target_runtime=current.target_runtime,
                protocol=current.protocol,
                plc_address=current.plc_address,
                io_config_json=current.io_config_json,
                deploy_status="running" if result.get("status") == "passed" else current.deploy_status,
                validation_status=current.validation_status,
                deployed_version=current.deployed_version,
                artifact_path=current.artifact_path,
                last_error=result.get("message") if result.get("status") == "failed" else current.last_error,
            )
    return result


@router.post("/stop")
def stop_runtime() -> dict[str, Any]:
    result = runtime_manager.stop()
    status = runtime_manager.status()
    project_id = status.get("project_id")
    if project_id:
        current = runtime_deployment_store.get_latest(project_id)
        if current:
            runtime_deployment_store.upsert_project_deployment(
                project_id=project_id,
                target_runtime=current.target_runtime,
                protocol=current.protocol,
                plc_address=current.plc_address,
                io_config_json=current.io_config_json,
                deploy_status="stopped" if result.get("status") == "passed" else current.deploy_status,
                validation_status=current.validation_status,
                deployed_version=current.deployed_version,
                artifact_path=current.artifact_path,
                last_error=result.get("message") if result.get("status") == "failed" else current.last_error,
            )
    return result


@router.post("/restart")
def restart_runtime() -> dict[str, Any]:
    return runtime_manager.restart()


@router.get("/tags")
def get_runtime_tags() -> dict[str, Any]:
    return runtime_telemetry.get_all_tags()


@router.get("/deployments/latest")
def get_latest_runtime_deployment(project_id: str = Query(...)) -> dict[str, Any]:
    project_service.ensure_project(project_id)
    deployment = runtime_deployment_store.get_latest(project_id)
    return {
        "project_id": project_id,
        "deployment": deployment.model_dump() if deployment else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/state", response_model=RuntimeStateResponse)
def get_runtime_state(project_id: str = Query(...)) -> RuntimeStateResponse:
    project_service.ensure_project(project_id)
    deployment = runtime_deployment_store.get_latest(project_id)
    manager_state = runtime_manager.status()
    live_runtime = manager_state.get("runtime") if isinstance(manager_state.get("runtime"), dict) else {}
    active_project = manager_state.get("project_id")
    live_status = str(live_runtime.get("status") or "stopped")

    # Persisted deployment metadata is engineering state-of-record; live runtime process info is transient and reconciled on each request.

    if active_project == project_id and live_status == "running":
        runtime_state = "running"
    elif deployment and deployment.deploy_status == "failed":
        runtime_state = "failed"
    elif deployment and deployment.deploy_status in {"deployed", "running", "stopped"}:
        runtime_state = "stopped"
    else:
        runtime_state = "idle"

    return RuntimeStateResponse(
        project_id=project_id,
        runtime_state=runtime_state,
        deployment=deployment,
        live_runtime=live_runtime,
    )


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
