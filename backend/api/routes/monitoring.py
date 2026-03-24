from fastapi import APIRouter

from runtime_engine.runtime_signal_state import runtime_signal_state
from services.behavior_loader_patch import push_runtime_snapshot_into_behavior_layer
from services.replay_service import replay_service
from services.simulation_service import simulation_service

router = APIRouter(prefix="/projects/{project_id}/monitoring", tags=["monitoring"])


@router.get("/summary")
def monitoring_summary(project_id: str) -> dict[str, object]:
    snapshot = runtime_signal_state.get_project_snapshot(project_id)
    current_values = snapshot.get("current_values", {}) if isinstance(snapshot, dict) else {}
    if isinstance(current_values, dict) and current_values:
        push_runtime_snapshot_into_behavior_layer(
            {
                "project_id": project_id,
                "current_values": current_values,
            }
        )

    simulation = simulation_service.latest(project_id)
    replay = replay_service.get_replay(project_id=project_id, start_minutes_ago=10, points=3)

    return {
        "project_id": project_id,
        "simulation": simulation["metrics"],
        "last_events": replay["timeline"],
        "dashboard": {
            "grafana_url": f"/grafana/{project_id}",
            "prometheus_job": f"crosslayerx_{project_id}",
        },
    }
