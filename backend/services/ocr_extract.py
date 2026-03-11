from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OCRPageResult:
    page_number: int
    text: str
    confidence: float


class OCRExtractService:
    """OCR adapter with deterministic fallback and optional pytesseract/Tesseract runtime."""

    @staticmethod
    def _extract_with_tesseract(file_path: str) -> list[OCRPageResult]:
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:
            return []

        path = Path(file_path)
        if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
            return []

        image = Image.open(path)
        text = pytesseract.image_to_string(image) or ""
        confidence = 0.9 if text.strip() else 0.0
        return [OCRPageResult(page_number=1, text=text.strip(), confidence=confidence)]

    def extract(self, file_path: str) -> list[OCRPageResult]:
        tesseract_pages = self._extract_with_tesseract(file_path)
        if tesseract_pages:
            return tesseract_pages

        path = Path(file_path)
        if path.suffix.lower() == ".txt" and path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                return [OCRPageResult(page_number=1, text=text, confidence=0.5)]
        return []


ocr_extract_service = OCRExtractService()
