from fastapi import APIRouter, HTTPException

from models.logic import ControlRule, LogicGenerateRequest, LogicGenerationResult
from services.logic_service import logic_service

router = APIRouter(prefix="/projects/{project_id}/logic", tags=["logic"])


@router.post("/generate", response_model=LogicGenerationResult)
def generate_logic(project_id: str, payload: LogicGenerateRequest) -> LogicGenerationResult:
    return logic_service.generate(project_id, strategy=payload.strategy)


@router.get("", response_model=LogicGenerationResult)
def list_logic(project_id: str) -> LogicGenerationResult:
    return logic_service.list_rules(project_id)


@router.get("/latest", response_model=LogicGenerationResult)
def latest_logic(project_id: str) -> LogicGenerationResult:
    return logic_service.get_latest(project_id)


@router.get("/runs/{logic_run_id}", response_model=LogicGenerationResult)
def get_logic_run(project_id: str, logic_run_id: str) -> LogicGenerationResult:
    result = logic_service.get_run(project_id, logic_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Logic run not found: {logic_run_id}")
    return result


@router.get("/rules/{rule_id}", response_model=ControlRule)
def get_logic_rule(project_id: str, rule_id: str) -> ControlRule:
    rule = logic_service.get_rule(project_id, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Control rule not found: {rule_id}")
    return rule
