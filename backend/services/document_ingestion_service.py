from __future__ import annotations

import logging


class DocumentIngestionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def ingest_batch(self, files: list[dict]) -> dict[str, list[dict]]:
        pid_files = [item for item in files if item.get("document_type") == "pid_pdf"]
        narrative_files = [item for item in files if item.get("document_type") == "control_narrative"]
        unknown_files = [item for item in files if item.get("document_type") == "unknown_document"]

        self.logger.info(
            "Ingestion complete: pid_files=%s narrative_files=%s unknown_files=%s",
            len(pid_files),
            len(narrative_files),
            len(unknown_files),
        )
        return {
            "pid_files": pid_files,
            "narrative_files": narrative_files,
            "unknown_files": unknown_files,
        }


document_ingestion_service = DocumentIngestionService()
