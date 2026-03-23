from __future__ import annotations

from fastapi import APIRouter

from models.pid_reconciliation import (
    PIDApplyUpdateRequest,
    PIDApplyUpdateResponse,
    PIDReconcileRequest,
    PIDReconcileSummary,
)
from services.pid_reconciliation_service import pid_reconciliation_service

router = APIRouter(prefix="/pid", tags=["pid-reconciliation"])


@router.post("/reconcile", response_model=PIDReconcileSummary)
def reconcile_pid(payload: PIDReconcileRequest) -> PIDReconcileSummary:
    dataset = [item.model_dump(mode="json") for item in payload.dataset]
    return pid_reconciliation_service.reconcile(dataset=dataset, similarity_threshold=payload.similarity_threshold)


@router.get("/changes", response_model=PIDReconcileSummary)
def get_pid_changes() -> PIDReconcileSummary:
    return pid_reconciliation_service.get_changes()


@router.post("/apply-update", response_model=PIDApplyUpdateResponse)
def apply_pid_update(payload: PIDApplyUpdateRequest) -> PIDApplyUpdateResponse:
    return pid_reconciliation_service.apply_update(
        allow_conflicts=payload.allow_conflicts,
        force_apply_on_validation_warnings=payload.force_apply_on_validation_warnings,
    )
