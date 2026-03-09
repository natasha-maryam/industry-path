from fastapi import APIRouter

from models.logic import LogicArtifact, LogicGenerateRequest
from services.logic_service import logic_service

router = APIRouter(prefix="/projects/{project_id}/logic", tags=["logic"])


@router.post("/generate", response_model=LogicArtifact)
def generate_logic(project_id: str, payload: LogicGenerateRequest) -> LogicArtifact:
    return logic_service.generate(project_id, strategy=payload.strategy)


@router.get("/latest", response_model=LogicArtifact)
def latest_logic(project_id: str) -> LogicArtifact:
    return logic_service.get_latest(project_id)
