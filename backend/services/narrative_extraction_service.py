from __future__ import annotations

import logging
import re
from pathlib import Path

from models.pipeline import RawDocumentChunk


SECTION_HINTS = (
    "control philosophy",
    "interlock",
    "alarm",
    "startup",
    "shutdown",
    "mode",
    "operation",
)


class NarrativeExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def extract(self, files: list[dict], path_resolver) -> list[RawDocumentChunk]:
        chunks: list[RawDocumentChunk] = []
        for file in files:
            file_path = path_resolver(file["file_path"])
            chunks.extend(self._extract_file(file, file_path))
        self.logger.info("Narrative extraction generated %s chunks", len(chunks))
        return chunks

    def _extract_file(self, file: dict, file_path: Path) -> list[RawDocumentChunk]:
        if file_path.suffix.lower() == ".txt":
            text = file_path.read_text(errors="ignore") if file_path.exists() else ""
            return self._split_to_chunks(file, text, 1)

        if file_path.suffix.lower() != ".pdf":
            text = file_path.read_text(errors="ignore") if file_path.exists() else ""
            return self._split_to_chunks(file, text, 1)

        file_chunks: list[RawDocumentChunk] = []
        try:
            import fitz  # type: ignore

            with fitz.open(file_path) as doc:
                for page_index, page in enumerate(doc, start=1):
                    page_text = page.get_text("text") or ""
                    if len(page_text.strip()) < 24:
                        try:
                            import pytesseract  # type: ignore
                            from PIL import Image  # type: ignore

                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                            mode = "RGB" if pix.alpha == 0 else "RGBA"
                            image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                            page_text = f"{page_text}\n{pytesseract.image_to_string(image)}".strip()
                        except Exception:
                            pass

                    file_chunks.extend(self._split_to_chunks(file, page_text, page_index))
        except Exception:
            text = file_path.read_text(errors="ignore") if file_path.exists() else ""
            file_chunks.extend(self._split_to_chunks(file, text, 1))

        return file_chunks

    def _split_to_chunks(self, file: dict, text: str, page_number: int) -> list[RawDocumentChunk]:
        chunks: list[RawDocumentChunk] = []
        current_section = "general"
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            lowered = line.lower()
            if any(hint in lowered for hint in SECTION_HINTS) and len(line) < 100:
                current_section = re.sub(r"\s+", "_", lowered)

            chunks.append(
                RawDocumentChunk(
                    file_id=file["id"],
                    file_name=file["original_name"],
                    document_type="control_narrative",
                    page_number=page_number,
                    text=line,
                    section=current_section,
                )
            )

        return chunks


narrative_extraction_service = NarrativeExtractionService()
