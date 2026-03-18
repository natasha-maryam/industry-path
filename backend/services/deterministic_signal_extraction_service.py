from __future__ import annotations

import logging
import re

from models.pipeline import EngineeringEntity, InferredRelationship, RawDocumentChunk
from services.signal_classification import device_type_from_tag, process_role_from_node, signal_type_from_tag


class DeterministicSignalExtractionService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._tag_pattern = re.compile(r"\b([A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b")
        self._narrative_control_patterns = [
            re.compile(
                r"\b(?P<actuator>[A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,80}?\b(STARTS|STOPS|OPENS|CLOSES|RUNS)\b.{0,50}?\b(WHEN|IF)\b.{0,60}?\b(?P<sensor>[A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?P<sensor>[A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b.{0,80}?\b(CONTROLS|COMMANDS|MODULATES|DRIVES|REGULATES)\b.{0,60}?\b(?P<actuator>[A-Z]{1,6}-?\d{1,5}[A-Z]{0,3})\b",
                re.IGNORECASE,
            ),
        ]
        self._threshold_pattern = re.compile(r"\b(>=|<=|>|<|ABOVE|BELOW)\s*(\d+(?:\.\d+)?)\s*%?\b", re.IGNORECASE)

    @staticmethod
    def _metadata_for_kind(kind: str) -> dict[str, object]:
        return {
            "equipment_type": kind,
            "signal_type": None,
            "instrument_role": None,
            "control_role": process_role_from_node(kind),
            "source": "P&ID + Narrative deterministic",
        }

    @staticmethod
    def _as_ref(chunk: RawDocumentChunk) -> str:
        return f"{chunk.file_name}:p{chunk.page_number}"

    def extract(
        self,
        entities: list[EngineeringEntity],
        pid_chunks: list[RawDocumentChunk],
        narrative_chunks: list[RawDocumentChunk],
    ) -> tuple[list[InferredRelationship], dict[str, dict[str, object]], list[str]]:
        entity_by_tag = {entity.id.upper(): entity for entity in entities}
        metadata: dict[str, dict[str, object]] = {}
        relationships: list[InferredRelationship] = []
        warnings: list[str] = []

        for chunk in [*pid_chunks, *narrative_chunks]:
            seen_on_chunk: set[str] = set()
            tags = [item.upper() for item in self._tag_pattern.findall(chunk.text.upper())]
            for tag in tags:
                entity = entity_by_tag.get(tag)
                if entity is None:
                    continue
                kind = device_type_from_tag(tag, entity.canonical_type)
                metadata.setdefault(entity.id, {})
                base = self._metadata_for_kind(kind)
                base["signal_type"] = signal_type_from_tag(tag, entity.canonical_type)
                base["instrument_role"] = "measurement" if base["signal_type"] == "analog" else "switch" if base["signal_type"] == "digital" and process_role_from_node(kind) == "sensor" else None
                metadata[entity.id].update({k: v for k, v in base.items() if v is not None})
                if tag in seen_on_chunk:
                    continue
                seen_on_chunk.add(tag)

            if chunk.document_type != "pid_pdf":
                continue

            for left, right in zip(tags, tags[1:]):
                source = entity_by_tag.get(left)
                target = entity_by_tag.get(right)
                if source is None or target is None or source.id == target.id:
                    continue

                relationships.append(
                    InferredRelationship(
                        relationship_type="CONNECTED_TO",
                        source_entity=source.id,
                        target_entity=target.id,
                        confidence_score=0.61,
                        confidence_level="MEDIUM",
                        inference_source="heuristic",
                        explanation="Deterministic P&ID adjacency relationship.",
                        source_references=[self._as_ref(chunk)],
                    )
                )

                if process_role_from_node(source.canonical_type) == "sensor":
                    relationships.append(
                        InferredRelationship(
                            relationship_type="MEASURES",
                            source_entity=source.id,
                            target_entity=target.id,
                            confidence_score=0.67,
                            confidence_level="MEDIUM",
                            inference_source="heuristic",
                            explanation="Deterministic sensor-to-neighbor measurement inference.",
                            source_references=[self._as_ref(chunk)],
                        )
                    )

        for chunk in narrative_chunks:
            upper = chunk.text.upper()
            for pattern in self._narrative_control_patterns:
                for match in pattern.finditer(upper):
                    sensor_tag = match.group("sensor").upper()
                    actuator_tag = match.group("actuator").upper()
                    sensor = entity_by_tag.get(sensor_tag)
                    actuator = entity_by_tag.get(actuator_tag)
                    if sensor is None or actuator is None:
                        continue

                    threshold = self._threshold_pattern.search(upper)
                    condition = f" {threshold.group(1)} {threshold.group(2)}" if threshold else ""
                    control_phrase = f"{sensor.id}{condition} -> {actuator.id}"

                    metadata.setdefault(sensor.id, {}).setdefault("controls", [])
                    if actuator.id not in metadata[sensor.id]["controls"]:
                        metadata[sensor.id]["controls"].append(actuator.id)

                    metadata.setdefault(actuator.id, {}).setdefault("controlled_by", [])
                    if sensor.id not in metadata[actuator.id]["controlled_by"]:
                        metadata[actuator.id]["controlled_by"].append(sensor.id)

                    metadata.setdefault(actuator.id, {}).setdefault("control_path", [])
                    if control_phrase not in metadata[actuator.id]["control_path"]:
                        metadata[actuator.id]["control_path"].append(control_phrase)

                    relationships.append(
                        InferredRelationship(
                            relationship_type="CONTROLS",
                            source_entity=sensor.id,
                            target_entity=actuator.id,
                            confidence_score=0.9,
                            confidence_level="HIGH",
                            inference_source="heuristic",
                            explanation="Deterministic narrative rule: sensor controls actuator.",
                            source_references=[self._as_ref(chunk)],
                        )
                    )

        for entity in entities:
            if entity.id not in metadata:
                continue
            metadata[entity.id].setdefault("process_unit", entity.process_unit or "unassigned")
            metadata[entity.id].setdefault("metadata_confidence", {})
            confidence_map = metadata[entity.id]["metadata_confidence"]
            if isinstance(confidence_map, dict):
                for key in ["equipment_type", "signal_type", "instrument_role", "control_role", "process_unit"]:
                    if metadata[entity.id].get(key) is not None:
                        confidence_map[key] = max(float(confidence_map.get(key, 0.0)), 0.79)

        if not relationships:
            warnings.append("Deterministic signal extraction produced no control or measurement relationships.")

        self.logger.info(
            "Deterministic signal extraction output: relationships=%s metadata=%s",
            len(relationships),
            len(metadata),
        )
        return relationships, metadata, warnings


deterministic_signal_extraction_service = DeterministicSignalExtractionService()