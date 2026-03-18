from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from services.graph_service import graph_service
from services.logic_service import logic_service
from services.simulation_service import simulation_service

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


@router.get("/simulation")
def export_simulation(project_id: str) -> JSONResponse:
    return JSONResponse(
        {
            "project_id": project_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "trace": simulation_service.trace(project_id),
            "issues": simulation_service.trace_analysis(project_id),
        }
    )


@router.get("/plant")
def export_plant(project_id: str) -> JSONResponse:
    graph = graph_service.get_graph(project_id)
    return JSONResponse(
        {
            "project_id": project_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "plant_graph": _to_jsonable(graph),
        }
    )


@router.get("/signals")
def export_signals(project_id: str) -> JSONResponse:
    signals = graph_service.get_plant_signals(project_id)
    return JSONResponse(
        {
            "project_id": project_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "signals": _to_jsonable(signals),
        }
    )


@router.get("/io")
def export_io(project_id: str) -> JSONResponse:
    latest = logic_service.get_latest_io_mapping(project_id)
    return JSONResponse(
        {
            "project_id": project_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "io_mapping": _to_jsonable(latest) if latest else {},
        }
    )


@router.get("/bundle")
def export_bundle(project_id: str) -> StreamingResponse:
    logic = logic_service.get_latest(project_id)
    trace = simulation_service.trace(project_id)
    issues = simulation_service.trace_analysis(project_id)
    graph = graph_service.get_graph(project_id)
    signals = graph_service.get_plant_signals(project_id)
    io_mapping = logic_service.get_latest_io_mapping(project_id)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("logic.st", getattr(logic, "code", "") or "")
        archive.writestr("simulation.json", json.dumps({"trace": trace, "issues": issues}, indent=2, default=str))
        archive.writestr("plant.json", json.dumps(_to_jsonable(graph), indent=2, default=str))
        archive.writestr("signals.json", json.dumps(_to_jsonable(signals), indent=2, default=str))
        archive.writestr("io_mapping.json", json.dumps(_to_jsonable(io_mapping) if io_mapping else {}, indent=2, default=str))

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{project_id}_engineering_bundle.zip"'},
    )
