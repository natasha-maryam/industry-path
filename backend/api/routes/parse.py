from fastapi import APIRouter

from models.parse import ParseBatchRequest, ParseJobStatusResponse, ParseSuggestionsResponse
from services.parse_service import parse_service

router = APIRouter(prefix="/projects/{project_id}/parse", tags=["parse"])


@router.post("")
def parse_project(project_id: str, payload: ParseBatchRequest | None = None) -> dict[str, object]:
    file_ids = payload.file_ids if payload else []
    return parse_service.parse_project(project_id, file_ids=file_ids)


@router.get("/jobs/{parse_job_id}", response_model=ParseJobStatusResponse)
def get_parse_job_status(project_id: str, parse_job_id: str) -> ParseJobStatusResponse:
    return ParseJobStatusResponse(**parse_service.get_parse_job_status(project_id, parse_job_id))


@router.get("/batches/{parse_batch_id}/suggestions", response_model=ParseSuggestionsResponse)
def get_parse_suggestions(project_id: str, parse_batch_id: str) -> ParseSuggestionsResponse:
    return ParseSuggestionsResponse(**parse_service.get_low_confidence_suggestions(project_id, parse_batch_id))
