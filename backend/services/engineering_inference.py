from __future__ import annotations

import logging
import re
import sys
from collections import defaultdict

import pandas as pd

from models.pipeline import EngineeringEntity, InferredRelationship, RawDocumentChunk
from services.deep_extraction_service import deep_extraction_service

if sys.version_info < (3, 14):
    try:
        import spacy
    except Exception:  # pragma: no cover
        spacy = None
else:  # pragma: no cover
    spacy = None

try:
    from rapidfuzz import fuzz
except Exception:  # pragma: no cover
    fuzz = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:  # pragma: no cover
    TfidfVectorizer = None


class EngineeringInferenceService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._tag_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b")
        self._power_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,48}?\b(\d+(?:\.\d+)?)\s*(HP|KW)\b", re.IGNORECASE)
        self._flow_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,48}?\b(\d+(?:\.\d+)?)\s*(M3/H|L/S|GPM)\b", re.IGNORECASE)
        self._head_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,48}?\bHEAD\s*[:=]?\s*(\d+(?:\.\d+)?)\s*M\b", re.IGNORECASE)
        self._control_pattern = re.compile(
            r"\b(?P<actuator>[A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,120}?\b(STARTS|OPENS|CLOSES|RUNS)\b.{0,120}?\b(?P<sensor>[A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b",
            re.IGNORECASE,
        )
        self._condition_pattern = re.compile(r"\b(>|<|>=|<=)\s*(\d+(?:\.\d+)?)%?\b")
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
    def _instrument_from_tag(tag: str) -> str | None:
        prefix = tag.upper().split("-")[0]
        if prefix.startswith("LT"):
            return "level_transmitter"
        if prefix.startswith("FT"):
            return "flow_transmitter"
        if prefix.startswith("PT"):
            return "pressure_transmitter"
        if prefix.startswith("TT"):
            return "temperature_transmitter"
        if prefix.startswith("LSH"):
            return "level_switch_high"
        if prefix.startswith("LS"):
            return "level_switch"
        return None

    @staticmethod
    def _default_template(canonical_type: str) -> dict[str, object]:
        templates: dict[str, dict[str, object]] = {
            "pump": {"control_role": "actuator", "signal_type": "digital", "power_rating": "unknown"},
            "valve": {"control_role": "actuator", "signal_type": "digital"},
            "control_valve": {"control_role": "actuator", "signal_type": "analog"},
            "blower": {"control_role": "actuator", "signal_type": "digital", "power_rating": "unknown"},
            "flow_transmitter": {"control_role": "sensor", "instrument_role": "measurement", "signal_type": "analog"},
            "level_transmitter": {"control_role": "sensor", "instrument_role": "measurement", "signal_type": "analog"},
            "pressure_transmitter": {"control_role": "sensor", "instrument_role": "measurement", "signal_type": "analog"},
            "level_switch": {"control_role": "sensor", "instrument_role": "switch", "signal_type": "digital"},
        }
        return dict(templates.get(canonical_type, {}))

    def infer(
        self,
        entities: list[EngineeringEntity],
        pid_chunks: list[RawDocumentChunk],
        narrative_chunks: list[RawDocumentChunk],
        pid_parser_relationships: list[InferredRelationship],
        pid_parser_metadata: dict[str, dict[str, object]],
        rule_bundle: dict[str, list],
    ) -> tuple[list[InferredRelationship], dict[str, dict[str, object]], list[str]]:
        warnings: list[str] = []
        deep_relationships, deep_metadata, deep_warnings = deep_extraction_service.extract(
            entities=entities,
            pid_chunks=pid_chunks,
            narrative_chunks=narrative_chunks,
        )
        warnings.extend(deep_warnings)

        entity_by_id = {entity.id.upper(): entity for entity in entities}
        metadata: dict[str, dict[str, object]] = {entity.id: self._default_template(entity.canonical_type) for entity in entities}
        property_confidence: dict[str, dict[str, float]] = defaultdict(dict)

        for entity in entities:
            metadata[entity.id].setdefault("device_type", entity.canonical_type)
            metadata[entity.id].setdefault("process_unit", entity.process_unit or "unassigned")

        for tag, values in pid_parser_metadata.items():
            entity = entity_by_id.get(tag.upper())
            if entity is None:
                continue
            metadata[entity.id].update(values)
            for key in values.keys():
                property_confidence[entity.id][key] = max(property_confidence[entity.id].get(key, 0.0), 0.7)

        for entity_id, values in deep_metadata.items():
            metadata.setdefault(entity_id, {})
            metadata[entity_id].update(values)
            for key in values.keys():
                property_confidence[entity_id][key] = max(property_confidence[entity_id].get(key, 0.0), 0.66)

        all_chunks = [*pid_chunks, *narrative_chunks]
        full_text = "\n".join(chunk.text for chunk in all_chunks)

        for match in self._power_pattern.finditer(full_text.upper()):
            tag, value, unit = match.groups()
            entity = entity_by_id.get(tag.upper())
            if entity is None:
                continue
            metadata[entity.id]["power_rating"] = f"{value}{unit.lower()}"
            property_confidence[entity.id]["power_rating"] = max(property_confidence[entity.id].get("power_rating", 0.0), 0.82)

        for match in self._flow_pattern.finditer(full_text.upper()):
            tag, value, unit = match.groups()
            entity = entity_by_id.get(tag.upper())
            if entity is None:
                continue
            metadata[entity.id]["flow_rate"] = f"{value}{unit.lower()}"
            property_confidence[entity.id]["flow_rate"] = max(property_confidence[entity.id].get("flow_rate", 0.0), 0.78)

        for match in self._head_pattern.finditer(full_text.upper()):
            tag, value = match.groups()
            entity = entity_by_id.get(tag.upper())
            if entity is None:
                continue
            metadata[entity.id]["head"] = f"{value}m"
            property_confidence[entity.id]["head"] = max(property_confidence[entity.id].get("head", 0.0), 0.76)

        inferred_relationships: list[InferredRelationship] = [*pid_parser_relationships, *deep_relationships]

        for chunk in narrative_chunks:
            text = chunk.text.upper()
            for match in self._control_pattern.finditer(text):
                actuator_tag = match.group("actuator").upper()
                sensor_tag = match.group("sensor").upper()
                actuator = entity_by_id.get(actuator_tag)
                sensor = entity_by_id.get(sensor_tag)
                if actuator is None or sensor is None:
                    continue

                inferred_relationships.append(
                    InferredRelationship(
                        relationship_type="CONTROLS",
                        source_entity=sensor.id,
                        target_entity=actuator.id,
                        confidence_score=0.86,
                        confidence_level="HIGH",
                        inference_source="heuristic",
                        explanation="Narrative pattern inferred sensor-to-actuator control path.",
                        source_references=[f"{chunk.file_name}:p{chunk.page_number}"],
                    )
                )

                sensor_controls = metadata.setdefault(sensor.id, {}).setdefault("controls", [])
                if isinstance(sensor_controls, list) and actuator.id not in sensor_controls:
                    sensor_controls.append(actuator.id)
                    property_confidence[sensor.id]["controls"] = max(property_confidence[sensor.id].get("controls", 0.0), 0.9)

                actuator_controlled_by = metadata.setdefault(actuator.id, {}).setdefault("controlled_by", [])
                if isinstance(actuator_controlled_by, list) and sensor.id not in actuator_controlled_by:
                    actuator_controlled_by.append(sensor.id)
                    property_confidence[actuator.id]["controlled_by"] = max(property_confidence[actuator.id].get("controlled_by", 0.0), 0.88)

                condition = self._condition_pattern.search(text)
                control_phrase = f"{sensor.id} → {actuator.id}"
                if condition:
                    control_phrase = f"{sensor.id} ({condition.group(1)} {condition.group(2)}) → {actuator.id}"

                control_path = metadata.setdefault(actuator.id, {}).setdefault("control_path", [])
                if isinstance(control_path, list) and control_phrase not in control_path:
                    control_path.append(control_phrase)
                    property_confidence[actuator.id]["control_path"] = max(property_confidence[actuator.id].get("control_path", 0.0), 0.9)

        if self._spacy_nlp is not None and narrative_chunks:
            try:
                sample_text = "\n".join(chunk.text for chunk in narrative_chunks[:12])
                doc = self._spacy_nlp(sample_text)
                noun_phrases = [chunk.text for chunk in doc.noun_chunks][:50]
                if noun_phrases:
                    vectorize_candidates = noun_phrases
                    if TfidfVectorizer is not None:
                        matrix = TfidfVectorizer(max_features=24).fit_transform(vectorize_candidates)
                        density_score = float(matrix.nnz) / float(matrix.shape[0] * matrix.shape[1]) if matrix.shape[0] and matrix.shape[1] else 0.0
                    else:
                        density_score = min(1.0, len(noun_phrases) / 100.0)

                    for entity in entities:
                        metadata.setdefault(entity.id, {})["narrative_context_score"] = f"{density_score:.2f}"
                        property_confidence[entity.id]["narrative_context_score"] = max(property_confidence[entity.id].get("narrative_context_score", 0.0), 0.62)
            except Exception:
                warnings.append("Engineering inference: spaCy narrative pass skipped")

        if fuzz is not None and rule_bundle.get("control_loops"):
            for loop in rule_bundle.get("control_loops", []):
                loop_name = getattr(loop, "name", "")
                for entity in entities:
                    score = fuzz.partial_ratio(loop_name.lower(), entity.id.lower())
                    if score >= 70:
                        linked_logic = metadata.setdefault(entity.id, {}).setdefault("linked_logic", [])
                        if isinstance(linked_logic, list) and loop_name not in linked_logic:
                            linked_logic.append(loop_name)
                            property_confidence[entity.id]["linked_logic"] = max(property_confidence[entity.id].get("linked_logic", 0.0), 0.72)

        for entity in entities:
            instrument_guess = self._instrument_from_tag(entity.id)
            if instrument_guess and metadata[entity.id].get("equipment_type") in {None, "equipment"}:
                metadata[entity.id]["equipment_type"] = instrument_guess
                property_confidence[entity.id]["equipment_type"] = max(property_confidence[entity.id].get("equipment_type", 0.0), 0.8)

            if instrument_guess and metadata[entity.id].get("instrument_role") in {None, "n/a"}:
                metadata[entity.id]["instrument_role"] = "measurement" if "transmitter" in instrument_guess else "switch"
                property_confidence[entity.id]["instrument_role"] = max(property_confidence[entity.id].get("instrument_role", 0.0), 0.78)

            if instrument_guess and metadata[entity.id].get("signal_type") in {None, "n/a"}:
                metadata[entity.id]["signal_type"] = "analog" if "transmitter" in instrument_guess else "digital"
                property_confidence[entity.id]["signal_type"] = max(property_confidence[entity.id].get("signal_type", 0.0), 0.76)

            metadata[entity.id]["metadata_confidence"] = {
                key: round(value, 2) for key, value in sorted(property_confidence.get(entity.id, {}).items())
            }

        self.logger.info(
            "Engineering inference output: relationships=%s metadata=%s",
            len(inferred_relationships),
            len(metadata),
        )
        return inferred_relationships, metadata, warnings


engineering_inference_service = EngineeringInferenceService()
