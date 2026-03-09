from fastapi import APIRouter, Query

from models.logic import DeployResult
from services.deploy_service import deploy_service

router = APIRouter(prefix="/projects/{project_id}/deploy", tags=["deploy"])


@router.post("", response_model=DeployResult)
def deploy(project_id: str, runtime: str = Query(default="OpenPLC")) -> DeployResult:
    return deploy_service.deploy(project_id=project_id, runtime=runtime)
