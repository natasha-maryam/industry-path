from fastapi import APIRouter, Query

from services.replay_service import replay_service

router = APIRouter(prefix="/projects/{project_id}/replay", tags=["replay"])


@router.get("")
def replay(project_id: str, start_minutes_ago: int = Query(default=5, ge=1, le=120)) -> dict[str, object]:
    return replay_service.get_replay(project_id=project_id, start_minutes_ago=start_minutes_ago)
