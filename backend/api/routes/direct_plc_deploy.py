from __future__ import annotations

from fastapi import APIRouter

from models.direct_plc_deployment import DirectPLCDeploymentRequest, DirectPLCDeploymentResponse
from services.direct_plc_deployment_service import direct_plc_deployment_service

router = APIRouter(prefix="/direct-plc", tags=["direct-plc-deployment"])


@router.post("/deploy", response_model=DirectPLCDeploymentResponse)
def deploy_direct_plc(payload: DirectPLCDeploymentRequest) -> DirectPLCDeploymentResponse:
    return direct_plc_deployment_service.deploy(payload)
