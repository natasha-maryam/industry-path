from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.file import UploadResult
from services.upload_service import upload_service

router = APIRouter(prefix="/projects/{project_id}/upload", tags=["uploads"])


@router.post("", response_model=UploadResult)
async def upload_documents(
    project_id: str,
    files: list[UploadFile] = File(...),
    document_types: list[str] | None = Form(default=None),
) -> UploadResult:
    try:
        return await upload_service.save_files(project_id, files, document_types)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
