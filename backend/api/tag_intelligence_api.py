from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from services.tag_intelligence import tag_intelligence_service


router = APIRouter(tags=["tag-intelligence"])


@router.get("/tag-intelligence")
def get_tag_intelligence(
    project_id: str | None = Query(default=None),
    category: str = Query(default="all"),
    search: str = Query(default=""),
) -> dict[str, object]:
    payload = tag_intelligence_service.query_rows(project_id=project_id, category=category, search=search)
    return {
        "success": True,
        "message": "Tag intelligence rows fetched.",
        "data": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/tag-intelligence/export/csv")
def export_tag_intelligence_csv(
    project_id: str | None = Query(default=None),
    category: str = Query(default="all"),
    search: str = Query(default=""),
) -> StreamingResponse:
    content = tag_intelligence_service.export_csv(project_id=project_id, category=category, search=search)
    filename = f"tag-intelligence-{category or 'all'}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tag-intelligence/export/json")
def export_tag_intelligence_json(
    project_id: str | None = Query(default=None),
    category: str = Query(default="all"),
    search: str = Query(default=""),
) -> StreamingResponse:
    content = tag_intelligence_service.export_json(project_id=project_id, category=category, search=search)
    filename = f"tag-intelligence-{category or 'all'}.json"
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
