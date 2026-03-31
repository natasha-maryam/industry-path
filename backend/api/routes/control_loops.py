from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from models.control_loop import ControlLoopDetectRequest, ControlLoopRecord
from services.control_loop_engine import control_loop_engine
from services.control_loop_store import control_loop_store
from services.project_service import project_service

router = APIRouter(prefix="/control-loops", tags=["control-loops"])
logger = logging.getLogger(__name__)


@router.post("/detect", response_model=list[ControlLoopRecord])
def detect_control_loops(payload: ControlLoopDetectRequest) -> list[ControlLoopRecord]:
    if not payload.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")
    project_service.ensure_project(payload.project_id)
    logger.info("Control loop detect request: project=%s", payload.project_id)
    loops = control_loop_engine.detect_and_store(payload.project_id)
    logger.info("Control loop detect response: project=%s loops=%s", payload.project_id, len(loops))
    return loops


@router.get("", response_model=list[ControlLoopRecord])
def list_control_loops(project_id: str | None = Query(default=None)) -> list[ControlLoopRecord]:
    if project_id:
        if not project_id.strip():
            raise HTTPException(status_code=400, detail="project_id cannot be empty")
        project_service.ensure_project(project_id)
    loops = control_loop_store.list_loops(project_id)
    logger.info("Control loop list response: project=%s loops=%s", project_id or "all", len(loops))
    return loops


@router.get("/debug/{project_id}")
def debug_control_loop_detection(project_id: str) -> dict[str, object]:
    if not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")
    project_service.ensure_project(project_id)
    snapshot = control_loop_engine.debug_snapshot(project_id)
    logger.info(
        "Control loop debug snapshot: project=%s sensors=%s processes=%s actuators=%s measures=%s controls=%s",
        project_id,
        snapshot.get("total_sensor_nodes", 0),
        snapshot.get("total_process_nodes", 0),
        snapshot.get("total_actuator_nodes", 0),
        snapshot.get("total_measures_edges", 0),
        snapshot.get("total_controls_edges", 0),
    )
    return snapshot


@router.get("/{loop_tag}", response_model=ControlLoopRecord)
def get_control_loop(loop_tag: str, project_id: str | None = Query(default=None)) -> ControlLoopRecord:
    if not loop_tag.strip():
        raise HTTPException(status_code=400, detail="loop_tag is required")
    if project_id:
        if not project_id.strip():
            raise HTTPException(status_code=400, detail="project_id cannot be empty")
        project_service.ensure_project(project_id)
    loop = control_loop_store.get_loop(loop_tag=loop_tag, project_id=project_id)
    if loop is None:
        raise HTTPException(status_code=404, detail=f"Control loop not found: {loop_tag}")
    logger.info("Control loop get response: project=%s loop=%s", project_id or "all", loop_tag)
    return loop
