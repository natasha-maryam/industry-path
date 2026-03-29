from __future__ import annotations

import logging
import re
from collections import defaultdict

from models.document_pipeline import SegmentedDocument, SegmentedDocumentBlock
from models.pipeline import RawDocumentChunk
from services.document_ingestion_service import document_ingestion_service
from services.narrative_extraction_service import narrative_extraction_service
from services.pid_extraction_service import pid_extraction_service


class DocumentSegmentationService:
    SECTION_PATTERN = re.compile(r"^[A-Z][A-Z0-9 /_-]{2,80}$")
    ZONE_PATTERN = re.compile(r"\b(zone|area|unit|train|skid|loop)\b", re.IGNORECASE)
    SPLIT_COLUMNS_PATTERN = re.compile(r"\s{2,}|\t+|\|+")
    TAG_PATTERN = re.compile(r"\b[A-Z]{1,6}[-_ ]?\d{1,5}[A-Z]{0,3}\b")

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def segment_documents(self, files: list[dict], resolve_file_path) -> tuple[list[SegmentedDocument], list[RawDocumentChunk], list[RawDocumentChunk]]:
        ingested = document_ingestion_service.ingest_batch(files)
        pid_chunks = pid_extraction_service.extract(ingested["pid_files"], resolve_file_path)
        narrative_input = [*ingested["narrative_files"], *ingested["unknown_files"]]
        narrative_chunks = narrative_extraction_service.extract(narrative_input, resolve_file_path)
        documents = self.segment_chunks([*pid_chunks, *narrative_chunks])
        return documents, pid_chunks, narrative_chunks

    def segment_chunks(self, chunks: list[RawDocumentChunk]) -> list[SegmentedDocument]:
        sections_by_document: dict[str, list[SegmentedDocumentBlock]] = defaultdict(list)
        file_names: dict[str, str] = {}
        doc_types: dict[str, str] = {}

        for chunk in chunks:
            file_names[chunk.file_id] = chunk.file_name
            doc_types[chunk.file_id] = chunk.document_type
            sections_by_document[chunk.file_id].extend(self._segment_chunk(chunk))

        documents = [
            SegmentedDocument(
                document_id=document_id,
                file_name=file_names.get(document_id, document_id),
                document_type=doc_types.get(document_id, "unknown_document"),
                sections=sorted(
                    sections,
                    key=lambda item: (item.page_number, item.block_type, item.block_id),
                ),
            )
            for document_id, sections in sorted(sections_by_document.items())
        ]
        self.logger.info("Document segmentation complete: documents=%s sections=%s", len(documents), sum(len(doc.sections) for doc in documents))
        return documents

    def flatten_sections(self, documents: list[SegmentedDocument]) -> list[SegmentedDocumentBlock]:
        return [section for document in documents for section in document.sections]

    def _segment_chunk(self, chunk: RawDocumentChunk) -> list[SegmentedDocumentBlock]:
        lines = [line.rstrip() for line in str(chunk.text or "").splitlines()]
        indexed_lines = [(index + 1, line.strip()) for index, line in enumerate(lines) if line.strip()]
        if not indexed_lines and str(chunk.text or "").strip():
            indexed_lines = [(1, str(chunk.text).strip())]

        blocks: list[SegmentedDocumentBlock] = []
        current_section = chunk.section or "general"
        current_zone = f"page_{chunk.page_number}"
        next_index = 1
        narrative_buffer: list[tuple[int, str]] = []
        table_buffer: list[tuple[int, str]] = []
        zone_buffer: list[tuple[int, str]] = []

        def flush_narrative() -> None:
            nonlocal next_index
            if not narrative_buffer:
                return
            line_numbers = [line_number for line_number, _ in narrative_buffer]
            text = "\n".join(line for _, line in narrative_buffer).strip()
            narrative_buffer.clear()
            if not text:
                return
            blocks.append(
                self._make_block(
                    chunk=chunk,
                    block_index=next_index,
                    block_type="narrative_section",
                    text=text,
                    section=current_section,
                    line_numbers=line_numbers,
                )
            )
            next_index += 1

        def flush_table() -> None:
            nonlocal next_index
            if not table_buffer:
                return
            line_numbers = [line_number for line_number, _ in table_buffer]
            raw_lines = [line for _, line in table_buffer]
            text = "\n".join(raw_lines).strip()
            table_buffer.clear()
            if not text:
                return
            blocks.append(
                self._make_block(
                    chunk=chunk,
                    block_index=next_index,
                    block_type="table",
                    text=text,
                    section=current_section,
                    zone_name=current_zone if chunk.document_type == "pid_pdf" else None,
                    table_rows=[self._split_table_row(line) for line in raw_lines],
                    line_numbers=line_numbers,
                )
            )
            next_index += 1

        def flush_zone() -> None:
            nonlocal next_index
            if chunk.document_type != "pid_pdf" or not zone_buffer:
                return
            line_numbers = [line_number for line_number, _ in zone_buffer]
            text = "\n".join(line for _, line in zone_buffer).strip()
            zone_buffer.clear()
            if not text:
                return
            blocks.append(
                self._make_block(
                    chunk=chunk,
                    block_index=next_index,
                    block_type="pid_zone",
                    text=text,
                    section=current_section,
                    zone_name=current_zone,
                    line_numbers=line_numbers,
                )
            )
            next_index += 1

        for line_number, line in indexed_lines:
            detected_section = self._detect_section_heading(line)
            detected_zone = self._detect_zone_name(line) if chunk.document_type == "pid_pdf" else None
            if detected_section:
                flush_table()
                flush_narrative()
                current_section = detected_section
                if detected_zone:
                    flush_zone()
                    current_zone = detected_zone
                continue

            if detected_zone and detected_zone != current_zone:
                flush_zone()
                current_zone = detected_zone

            if self._is_table_row(line):
                flush_narrative()
                table_buffer.append((line_number, line))
            else:
                flush_table()
                narrative_buffer.append((line_number, line))

            if chunk.document_type == "pid_pdf":
                zone_buffer.append((line_number, line))

        flush_table()
        flush_narrative()
        flush_zone()

        if not any(block.kind == "narrative" for block in blocks) and indexed_lines:
            line_numbers = [line_number for line_number, _ in indexed_lines]
            text = "\n".join(line for _, line in indexed_lines).strip()
            blocks.append(
                self._make_block(
                    chunk=chunk,
                    block_index=next_index,
                    block_type="narrative_section",
                    text=text,
                    section=current_section,
                    line_numbers=line_numbers,
                )
            )

        return blocks

    def _make_block(
        self,
        *,
        chunk: RawDocumentChunk,
        block_index: int,
        block_type: str,
        text: str,
        section: str | None,
        line_numbers: list[int],
        zone_name: str | None = None,
        table_rows: list[list[str]] | None = None,
    ) -> SegmentedDocumentBlock:
        block_id = f"{chunk.file_id}:{chunk.page_number}:{block_type}:{block_index}"
        kind = "narrative" if block_type == "narrative_section" else block_type
        metadata: dict[str, object] = {
            "section": section,
            "zone_name": zone_name,
            "source_references": [f"{chunk.file_name}:p{chunk.page_number}:{block_type}:{block_index}"],
            "source_span": {
                "line_start": min(line_numbers) if line_numbers else 1,
                "line_end": max(line_numbers) if line_numbers else 1,
            },
        }
        if table_rows:
            metadata["table_rows"] = table_rows

        return SegmentedDocumentBlock(
            section_id=block_id,
            block_id=block_id,
            file_id=chunk.file_id,
            file_name=chunk.file_name,
            document_id=chunk.file_id,
            document_type=chunk.document_type,
            kind=kind,
            page=chunk.page_number,
            page_number=chunk.page_number,
            block_type=block_type,
            text=text,
            bbox=chunk.bbox,
            metadata=metadata,
            section=section,
            zone_name=zone_name,
            table_rows=table_rows or [],
            source_references=list(metadata["source_references"]),
            ocr_used=bool(chunk.ocr_used),
        )

    def _detect_section_heading(self, line: str) -> str | None:
        normalized = re.sub(r"\s+", "_", line.strip().lower())
        if not normalized:
            return None
        if self._is_table_row(line):
            return None
        if len(self.TAG_PATTERN.findall(line)) >= 2:
            return None
        if self.SECTION_PATTERN.match(line.strip()) or any(token in normalized for token in ("control_philosophy", "interlock", "alarm", "startup", "shutdown", "mode", "operation")):
            return normalized[:96]
        return None

    def _detect_zone_name(self, line: str) -> str | None:
        if self.ZONE_PATTERN.search(line) is None:
            return None
        if len(line.strip()) > 64 or any(token in line for token in ".;:"):
            return None
        if len(self.TAG_PATTERN.findall(line)) >= 2:
            return None
        tokens = re.sub(r"[^A-Za-z0-9]+", "_", line.strip().lower()).strip("_")
        return tokens[:96] or None

    def _is_table_row(self, line: str) -> bool:
        if "|" in line or "\t" in line:
            return True
        if len(re.split(r"\s{2,}", line.strip())) >= 3:
            return True
        if line.count(",") >= 2:
            return True
        return False

    def _split_table_row(self, line: str) -> list[str]:
        columns = [part.strip() for part in self.SPLIT_COLUMNS_PATTERN.split(line) if part.strip()]
        if len(columns) < 2 and "," in line:
            columns = [part.strip() for part in line.split(",") if part.strip()]
        return columns or [line.strip()]


document_segmentation_service = DocumentSegmentationService()
