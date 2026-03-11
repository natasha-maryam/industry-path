from __future__ import annotations

from services.document_ingestion_service import document_ingestion_service


class DocumentIngestService:
    """Compatibility wrapper for deterministic document classification/ingest stage."""

    @staticmethod
    def ingest(files: list[dict]) -> dict[str, list[dict]]:
        return document_ingestion_service.ingest_batch(files)


document_ingest_service = DocumentIngestService()
