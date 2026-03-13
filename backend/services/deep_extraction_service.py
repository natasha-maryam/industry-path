from __future__ import annotations

import logging
import re
import sys
from collections import defaultdict

import pandas as pd

from models.pipeline import EngineeringEntity, InferredRelationship, RawDocumentChunk

try:
    import networkx as nx
except Exception:  # pragma: no cover - optional dependency
    nx = None

if sys.version_info < (3, 14):
    try:
        import spacy
    except Exception:  # pragma: no cover - optional dependency
        spacy = None
else:  # pragma: no cover - spaCy currently not compatible in this runtime
    spacy = None


class DeepExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._tag_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b")
        self._power_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,40}?\b(\d+(?:\.\d+)?)\s*(HP|KW)\b", re.IGNORECASE)
        self._relationship_patterns: list[tuple[re.Pattern[str], str, float, str]] = [
            (re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b\s+measures\s+\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "MEASURES", 0.82, "HIGH"),
            (re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b\s+feeds\s+\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "FEEDS", 0.84, "HIGH"),
            (re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b\s+controls\s+\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "CONTROLS", 0.82, "HIGH"),
            (re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b\s+connected\s+to\s+\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "CONNECTED_TO", 0.76, "MEDIUM"),
            (re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b\s+signal\s+to\s+\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b", re.IGNORECASE), "SIGNAL_TO", 0.74, "MEDIUM"),
        ]
        self._spacy_nlp = self._load_spacy_model()

    @staticmethod
    def _load_spacy_model():
        if spacy is None:
            return None
        for model_name in ("en_core_web_sm", "en_core_web_md"):
            try:
                return spacy.load(model_name)
            except Exception:
                continue
        return None

    @staticmethod
    def _infer_signal_type(canonical_type: str) -> str | None:
        sensor_types = {
            "flow_transmitter": "analog",
            "level_transmitter": "analog",
            "pressure_transmitter": "analog",
            "differential_pressure_transmitter": "analog",
            "analyzer": "analog",
            "level_switch": "digital",
        }
        actuator_types = {"pump": "digital", "valve": "digital", "control_valve": "analog", "blower": "digital"}
        if canonical_type in sensor_types:
            return sensor_types[canonical_type]
        if canonical_type in actuator_types:
            return actuator_types[canonical_type]
        return None

    @staticmethod
    def _infer_instrument_role(canonical_type: str) -> str | None:
        if canonical_type in {"flow_transmitter", "level_transmitter", "pressure_transmitter", "differential_pressure_transmitter"}:
            return "measurement"
        if canonical_type == "level_switch":
            return "switch"
        if canonical_type == "analyzer":
            return "analyzer"
        return None

    @staticmethod
    def _infer_control_role(canonical_type: str) -> str:
        if canonical_type in {"pump", "valve", "control_valve", "blower", "chemical_system_device"}:
            return "actuator"
        if canonical_type in {"flow_transmitter", "level_transmitter", "pressure_transmitter", "differential_pressure_transmitter", "level_switch", "analyzer"}:
            return "sensor"
        if canonical_type == "process_unit":
            return "process_unit"
        return "equipment"

    def extract(
        self,
        entities: list[EngineeringEntity],
        pid_chunks: list[RawDocumentChunk],
        narrative_chunks: list[RawDocumentChunk],
    ) -> tuple[list[InferredRelationship], dict[str, dict[str, str]], list[str]]:
        entity_by_id = {entity.id.upper(): entity for entity in entities}
        metadata: dict[str, dict[str, str]] = {}
        warnings: list[str] = []

        for entity in entities:
            metadata[entity.id] = {
                "device_type": entity.canonical_type,
                "process_unit": entity.process_unit or "unassigned",
                "signal_type": self._infer_signal_type(entity.canonical_type) or "n/a",
                "instrument_role": self._infer_instrument_role(entity.canonical_type) or "n/a",
                "control_role": self._infer_control_role(entity.canonical_type),
            }

        all_chunks = [*pid_chunks, *narrative_chunks]
        text_frame = pd.DataFrame(
            [{"file": chunk.file_name, "text": chunk.text, "page": chunk.page_number} for chunk in all_chunks]
        )

        if not text_frame.empty:
            tag_hits: dict[str, int] = defaultdict(int)
            for text in text_frame["text"].astype(str):
                for tag in self._tag_pattern.findall(text.upper()):
                    tag_hits[tag.upper()] += 1

            for entity in entities:
                metadata[entity.id]["tag_hits"] = str(tag_hits.get(entity.id.upper(), 0))

        relationships: list[InferredRelationship] = []
        for chunk in all_chunks:
            text = chunk.text or ""
            for pattern, relationship_type, confidence_score, confidence_level in self._relationship_patterns:
                for match in pattern.finditer(text):
                    raw_source, raw_target = match.group(1).upper(), match.group(2).upper()
                    source_entity = entity_by_id.get(raw_source)
                    target_entity = entity_by_id.get(raw_target)
                    if source_entity is None or target_entity is None:
                        continue
                    relationships.append(
                        InferredRelationship(
                            relationship_type=relationship_type,
                            source_entity=source_entity.id,
                            target_entity=target_entity.id,
                            confidence_score=confidence_score,
                            confidence_level=confidence_level,  # type: ignore[arg-type]
                            inference_source="heuristic",
                            explanation=f"Deep extraction inferred {relationship_type} from text pattern.",
                            source_references=[f"{chunk.file_name}:p{chunk.page_number}"],
                        )
                    )

            for power_match in self._power_pattern.finditer(text.upper()):
                raw_tag, rating_value, rating_unit = power_match.groups()
                entity = entity_by_id.get(raw_tag.upper())
                if entity is None:
                    continue
                metadata[entity.id]["power_rating"] = f"{rating_value}{rating_unit.lower()}"

            if self._spacy_nlp is not None and len(text) < 3000:
                try:
                    doc = self._spacy_nlp(text)
                    noun_count = sum(1 for token in doc if token.pos_ in {"NOUN", "PROPN"})
                    if noun_count > 0:
                        for tag in self._tag_pattern.findall(text.upper()):
                            entity = entity_by_id.get(tag.upper())
                            if entity is not None:
                                metadata[entity.id]["context_noun_density"] = str(noun_count)
                except Exception:
                    warnings.append(f"spaCy deep parse skipped for {chunk.file_name} page {chunk.page_number}")

        if nx is not None and relationships:
            graph = nx.DiGraph()
            for relationship in relationships:
                graph.add_edge(relationship.source_entity, relationship.target_entity, rel=relationship.relationship_type)

            for entity in entities:
                if entity.id not in graph:
                    continue
                outgoing = list(graph.successors(entity.id))
                if outgoing:
                    metadata[entity.id]["connected_to"] = ", ".join(outgoing[:4])

        self.logger.info(
            "Deep extraction output: metadata=%s inferred_relationships=%s",
            len(metadata),
            len(relationships),
        )
        return relationships, metadata, warnings


deep_extraction_service = DeepExtractionService()
