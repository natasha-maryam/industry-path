from fastapi import APIRouter

from services.simulation_service import simulation_service

router = APIRouter(prefix="/projects/{project_id}/simulation", tags=["simulation"])


@router.post("/run")
def run_simulation(project_id: str) -> dict[str, object]:
    return simulation_service.run(project_id)


@router.get("/trace")
def get_simulation_trace(project_id: str) -> dict[str, object]:
    return {
        "project_id": project_id,
        "trace": simulation_service.trace(project_id),
    }


@router.get("/analysis")
def get_simulation_analysis(project_id: str) -> dict[str, object]:
    return {
        "project_id": project_id,
        "issues": simulation_service.trace_analysis(project_id),
    }


@router.get("/simulation-trace")
def get_simulation_trace_list(project_id: str) -> list[dict[str, object]]:
    return simulation_service.trace(project_id)


@router.get("/simulation-analysis")
def get_simulation_analysis_list(project_id: str) -> list[dict[str, str]]:
    return simulation_service.trace_analysis(project_id)


@router.post("/simulation-trace/reset")
def reset_simulation_trace(project_id: str) -> dict[str, object]:
    simulation_service.reset_trace(project_id)
    return {
        "project_id": project_id,
        "status": "reset",
        "trace": [],
    }


@router.post("/simulation-trace/run")
def run_simulation_trace_cycle(project_id: str) -> dict[str, object]:
    trace = simulation_service.capture_trace(project_id, reset=False, step_ms=100, duration_ms=1200)
    return {
        "project_id": project_id,
        "status": "captured",
        "samples": len(trace),
        "trace": trace,
        "issues": simulation_service.trace_analysis(project_id),
    }
