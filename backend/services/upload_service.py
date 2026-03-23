from uuid import uuid4

from fastapi import UploadFile

from db.postgres import postgres_client
from models.file import ProjectFile, UploadResult
from services.project_service import project_service


class UploadService:
    _ALLOWED_DOCUMENT_TYPES = {
        "pid_pdf",
        "control_narrative",
        "unknown_document",
        "plc_project_file",
        "logic_export",
        "tag_list",
        "io_table",
    }

    @staticmethod
    def _infer_document_type(file_name: str) -> str:
        normalized = file_name.lower()
        if normalized.endswith((".l5x", ".acd", ".xml", ".ap16", ".project", ".tsproj")) or any(
            token in normalized for token in ("plc", "project", "codesys", "siemens", "rockwell", "beckhoff")
        ):
            return "plc_project_file"
        if normalized.endswith((".st", ".awl", ".scl")) or any(
            token in normalized for token in ("logic", "routine", "program", "export")
        ):
            return "logic_export"
        if normalized.endswith((".csv", ".txt")) and any(token in normalized for token in ("tag", "symbol", "variable")):
            return "tag_list"
        if normalized.endswith((".csv", ".xlsx", ".xls")) and any(token in normalized for token in ("io", "i_o", "channel", "terminal")):
            return "io_table"
        if any(token in normalized for token in ("p&id", "pid", "p_and_i", "p and i", "p_i_d", "p-i-d")):
            return "pid_pdf"
        if any(token in normalized for token in ("control narrative", "narrative", "control")):
            return "control_narrative"
        return "unknown_document"

    async def save_files(
        self,
        project_id: str,
        files: list[UploadFile],
        document_types: list[str] | None = None,
    ) -> UploadResult:
        paths = project_service.workspace_paths(project_id)
        project = project_service.get_project(project_id)
        records: list[ProjectFile] = []

        if document_types and len(document_types) != len(files):
            raise ValueError("document_types count must match files count")

        for upload in files:
            file_index = len(records)
            original_name = upload.filename or f"upload_{uuid4().hex[:8]}.bin"
            safe_name = f"{uuid4().hex}_{original_name}"
            destination = paths.documents / safe_name
            content = await upload.read()
            destination.write_bytes(content)
            relative_path = f"storage/projects/{project_id}/documents/{safe_name}"

            provided_type = document_types[file_index].strip() if document_types else ""
            document_type = provided_type or self._infer_document_type(original_name)
            if document_type not in self._ALLOWED_DOCUMENT_TYPES:
                document_type = "unknown_document"

            record = ProjectFile(
                project_id=project.id,
                original_name=original_name,
                stored_name=safe_name,
                file_type=upload.content_type or "application/octet-stream",
                document_type=document_type,
                file_path=relative_path,
                file_size=len(content),
            )

            postgres_client.execute(
                """
                INSERT INTO project_files (
                    id,
                    project_id,
                    original_name,
                    stored_name,
                    file_type,
                    document_type,
                    file_path,
                    file_size,
                    upload_status,
                    uploaded_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(record.id),
                    str(record.project_id),
                    record.original_name,
                    record.stored_name,
                    record.file_type,
                    record.document_type,
                    record.file_path,
                    record.file_size,
                    record.upload_status,
                    record.uploaded_at,
                ),
            )

            records.append(record)

        return UploadResult(project_id=project_id, files=records)


upload_service = UploadService()
