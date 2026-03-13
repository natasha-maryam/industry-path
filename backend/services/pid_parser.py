from __future__ import annotations

import logging
import re
from pathlib import Path

from models.pipeline import InferredRelationship

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional dependency
    fitz = None

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None

try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None


class PIDParserService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._tag_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b")
        self._instrument_map = {
            "LT": "level_transmitter",
            "FT": "flow_transmitter",
            "PT": "pressure_transmitter",
            "TT": "temperature_transmitter",
            "LSH": "level_switch_high",
            "LSL": "level_switch_low",
            "LS": "level_switch",
        }

    def _classify_tag(self, tag: str) -> str:
        normalized = tag.upper().replace("_", "-")
        prefix = normalized.split("-")[0]

        if prefix.startswith("P"):
            return "pump"
        if prefix.startswith("VAL") or prefix.startswith("XV") or prefix.startswith("CV"):
            return "valve"
        if prefix.startswith("TK") or prefix.startswith("TANK"):
            return "tank"
        if prefix.startswith("LIC") or prefix.startswith("FIC") or prefix.startswith("PIC"):
            return "controller"

        for instrument_prefix, instrument_type in self._instrument_map.items():
            if prefix.startswith(instrument_prefix):
                return instrument_type
        return "equipment"

    def _instrument_metadata(self, equipment_type: str) -> dict[str, object]:
        analog_types = {
            "level_transmitter",
            "flow_transmitter",
            "pressure_transmitter",
            "temperature_transmitter",
            "analyzer",
        }
        digital_types = {"level_switch", "level_switch_high", "level_switch_low"}

        signal_type = "analog" if equipment_type in analog_types else "digital" if equipment_type in digital_types else None
        instrument_role = "measurement" if equipment_type in analog_types else "switch" if equipment_type in digital_types else None
        control_role = "sensor" if equipment_type in analog_types.union(digital_types) else "actuator" if equipment_type in {"pump", "valve"} else "equipment"

        return {
            "signal_type": signal_type,
            "instrument_role": instrument_role,
            "control_role": control_role,
        }

    def parse(
        self,
        pid_files: list[dict],
        resolve_file_path,
    ) -> tuple[list[InferredRelationship], dict[str, dict[str, object]], list[str]]:
        warnings: list[str] = []
        metadata_by_tag: dict[str, dict[str, object]] = {}
        inferred_edges: list[InferredRelationship] = []

        for pid_file in pid_files:
            relative_path = pid_file.get("file_path")
            if not relative_path:
                continue

            full_path = resolve_file_path(relative_path)
            if not Path(full_path).exists():
                warnings.append(f"P&ID parser: file missing {relative_path}")
                continue

            page_tag_order: dict[int, list[str]] = {}

            if fitz is not None:
                try:
                    document = fitz.open(str(full_path))
                    for page_idx, page in enumerate(document, start=1):
                        tags_on_page: list[str] = []
                        blocks = page.get_text("blocks")
                        for block in blocks:
                            text = str(block[4] or "")
                            for tag in self._tag_pattern.findall(text.upper()):
                                tags_on_page.append(tag)
                                metadata_by_tag.setdefault(tag, {})
                                equipment_type = self._classify_tag(tag)
                                metadata_by_tag[tag].setdefault("equipment_type", equipment_type)
                                metadata_by_tag[tag].update({key: value for key, value in self._instrument_metadata(equipment_type).items() if value is not None})
                                metadata_by_tag[tag]["parser_source"] = "pymupdf"
                                metadata_by_tag[tag]["tag"] = tag

                        page_tag_order[page_idx] = tags_on_page

                        if cv2 is not None and np is not None and pytesseract is not None:
                            try:
                                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                image_bytes = np.frombuffer(pix.tobytes("png"), dtype=np.uint8)
                                image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
                                if image is not None:
                                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                                    edges = cv2.Canny(gray, 60, 160)
                                    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=30, maxLineGap=8)
                                    if lines is not None:
                                        metadata_by_tag.setdefault("_page_metrics_", {})
                                        metadata_by_tag["_page_metrics_"][f"page_{page_idx}_line_count"] = int(len(lines))

                                    ocr_text = pytesseract.image_to_string(gray)
                                    for tag in self._tag_pattern.findall(ocr_text.upper()):
                                        metadata_by_tag.setdefault(tag, {})
                                        equipment_type = self._classify_tag(tag)
                                        metadata_by_tag[tag].setdefault("equipment_type", equipment_type)
                                        metadata_by_tag[tag].update({key: value for key, value in self._instrument_metadata(equipment_type).items() if value is not None})
                                        metadata_by_tag[tag]["ocr_detected"] = True
                            except Exception:
                                warnings.append(f"P&ID parser: OpenCV/Tesseract step skipped for {pid_file.get('original_name')} page {page_idx}")
                except Exception as exc:
                    warnings.append(f"P&ID parser: PyMuPDF failed for {pid_file.get('original_name')}: {exc}")
            else:
                warnings.append("P&ID parser: PyMuPDF unavailable, using pdfplumber fallback")

            if pdfplumber is not None and not page_tag_order:
                try:
                    with pdfplumber.open(str(full_path)) as document:
                        for page_idx, page in enumerate(document.pages, start=1):
                            text = page.extract_text() or ""
                            tags = self._tag_pattern.findall(text.upper())
                            if tags:
                                page_tag_order[page_idx] = tags
                                for tag in tags:
                                    metadata_by_tag.setdefault(tag, {})
                                    equipment_type = self._classify_tag(tag)
                                    metadata_by_tag[tag].setdefault("equipment_type", equipment_type)
                                    metadata_by_tag[tag].update({key: value for key, value in self._instrument_metadata(equipment_type).items() if value is not None})
                                    metadata_by_tag[tag]["parser_source"] = "pdfplumber"
                except Exception as exc:
                    warnings.append(f"P&ID parser: pdfplumber failed for {pid_file.get('original_name')}: {exc}")

            for page_idx, tags in page_tag_order.items():
                if len(tags) < 2:
                    continue
                for left, right in zip(tags, tags[1:]):
                    if left == right:
                        continue
                    inferred_edges.append(
                        InferredRelationship(
                            relationship_type="CONNECTED_TO",
                            source_entity=left,
                            target_entity=right,
                            confidence_score=0.58,
                            confidence_level="LOW",
                            inference_source="heuristic",
                            explanation=f"P&ID adjacency from parser page {page_idx}.",
                            source_references=[f"{pid_file.get('original_name')}#page-{page_idx}"],
                        )
                    )

                for left, right in zip(tags, tags[1:]):
                    if left.startswith("P") and right.startswith(("TK", "TANK", "BAS", "CLR")):
                        inferred_edges.append(
                            InferredRelationship(
                                relationship_type="FEEDS",
                                source_entity=left,
                                target_entity=right,
                                confidence_score=0.7,
                                confidence_level="MEDIUM",
                                inference_source="heuristic",
                                explanation="Pump to vessel flow direction inferred from local P&ID sequence.",
                                source_references=[f"{pid_file.get('original_name')}#page-{page_idx}"],
                            )
                        )

                for left, right in zip(tags, tags[1:]):
                    left_type = self._classify_tag(left)
                    right_type = self._classify_tag(right)
                    if left_type in {
                        "level_transmitter",
                        "flow_transmitter",
                        "pressure_transmitter",
                        "temperature_transmitter",
                        "analyzer",
                        "level_switch",
                        "level_switch_high",
                        "level_switch_low",
                    } and right_type in {"pump", "valve", "tank", "controller", "equipment"}:
                        inferred_edges.append(
                            InferredRelationship(
                                relationship_type="MEASURES",
                                source_entity=left,
                                target_entity=right,
                                confidence_score=0.66,
                                confidence_level="MEDIUM",
                                inference_source="heuristic",
                                explanation="Instrument-to-equipment measurement relationship inferred from adjacent labels.",
                                source_references=[f"{pid_file.get('original_name')}#page-{page_idx}"],
                            )
                        )

        self.logger.info("PID parser output: metadata_tags=%s inferred_edges=%s", len(metadata_by_tag), len(inferred_edges))
        return inferred_edges, metadata_by_tag, warnings


pid_parser_service = PIDParserService()
