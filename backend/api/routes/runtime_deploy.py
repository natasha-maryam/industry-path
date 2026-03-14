from __future__ import annotations

from fastapi import APIRouter

from models.runtime_deploy import RuntimeDeployRequest, RuntimeDeployResponse
from services.runtime_deployer import runtime_deployer

router = APIRouter(tags=["runtime-deploy"])


@router.post("/deploy-runtime", response_model=RuntimeDeployResponse)
def deploy_runtime(payload: RuntimeDeployRequest) -> RuntimeDeployResponse:
    result = runtime_deployer.deploy_to_runtime(
        project_id=payload.project_id,
        workspace_path=payload.workspace_path,
        runtime_config=payload.runtime_config,
    )
    return RuntimeDeployResponse.model_validate(result)
