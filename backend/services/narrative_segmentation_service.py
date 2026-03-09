from __future__ import annotations

import logging
import re
from uuid import uuid4

from models.logic import NarrativeSentence
from services.narrative_extraction_service import narrative_extraction_service


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class NarrativeSegmentationService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def segment(self, project_id: str, files: list[dict], path_resolver) -> list[NarrativeSentence]:
        chunks = narrative_extraction_service.extract(files, path_resolver)
        sentences: list[NarrativeSentence] = []

        for chunk in chunks:
            text = (chunk.text or "").strip()
            if not text:
                continue

            segments = [item.strip(" ;\t") for item in _SENTENCE_SPLIT_RE.split(text) if item.strip()]
            if not segments:
                segments = [text]

            for segment in segments:
                sentences.append(
                    NarrativeSentence(
                        id=str(uuid4()),
                        project_id=project_id,
                        page_number=chunk.page_number,
                        section_heading=chunk.section,
                        text=segment,
                    )
                )

        self.logger.info("Narrative segmentation: files=%s chunks=%s sentences=%s", len(files), len(chunks), len(sentences))
        return sentences


narrative_segmentation_service = NarrativeSegmentationService()
