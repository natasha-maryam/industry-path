from __future__ import annotations

import logging
from pathlib import Path

from models.pipeline import RawDocumentChunk


class PIDExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def extract(self, files: list[dict], path_resolver) -> list[RawDocumentChunk]:
        chunks: list[RawDocumentChunk] = []
        for file in files:
            file_path = path_resolver(file["file_path"])
            chunks.extend(self._extract_file(file, file_path))
        self.logger.info("P&ID extraction generated %s chunks", len(chunks))
        return chunks

    def _extract_file(self, file: dict, file_path: Path) -> list[RawDocumentChunk]:
        file_chunks: list[RawDocumentChunk] = []
        if file_path.suffix.lower() == ".txt":
            text = file_path.read_text(errors="ignore") if file_path.exists() else ""
            file_chunks.append(
                RawDocumentChunk(
                    file_id=file["id"],
                    file_name=file["original_name"],
                    document_type="pid_pdf",
                    page_number=1,
                    text=text,
                    ocr_used=False,
                )
            )
            return file_chunks

        if file_path.suffix.lower() != ".pdf":
            text = file_path.read_text(errors="ignore") if file_path.exists() else ""
            file_chunks.append(
                RawDocumentChunk(
                    file_id=file["id"],
                    file_name=file["original_name"],
                    document_type="pid_pdf",
                    page_number=1,
                    text=text,
                    ocr_used=False,
                )
            )
            return file_chunks

        try:
            import fitz  # type: ignore

            with fitz.open(file_path) as doc:
                for page_index, page in enumerate(doc, start=1):
                    page_text = page.get_text("text") or ""
                    ocr_used = False
                    merged_text = page_text

                    if len(page_text.strip()) < 24:
                        try:
                            import pytesseract  # type: ignore
                            from PIL import Image  # type: ignore

                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            mode = "RGB" if pix.alpha == 0 else "RGBA"
                            image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                            ocr_text = pytesseract.image_to_string(image)
                            merged_text = f"{page_text}\n{ocr_text}".strip()
                            ocr_used = True
                        except Exception:
                            pass

                    file_chunks.append(
                        RawDocumentChunk(
                            file_id=file["id"],
                            file_name=file["original_name"],
                            document_type="pid_pdf",
                            page_number=page_index,
                            text=merged_text,
                            ocr_used=ocr_used,
                        )
                    )
        except Exception:
            text = file_path.read_text(errors="ignore") if file_path.exists() else ""
            file_chunks.append(
                RawDocumentChunk(
                    file_id=file["id"],
                    file_name=file["original_name"],
                    document_type="pid_pdf",
                    page_number=1,
                    text=text,
                    ocr_used=False,
                )
            )

        return file_chunks


pid_extraction_service = PIDExtractionService()
