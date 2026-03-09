from fastapi import APIRouter

from services.simulation_service import simulation_service

router = APIRouter(prefix="/projects/{project_id}/simulation", tags=["simulation"])


@router.post("/run")
def run_simulation(project_id: str) -> dict[str, object]:
    return simulation_service.run(project_id)
