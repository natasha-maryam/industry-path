from __future__ import annotations

import logging
import re
from collections import defaultdict

from models.document_pipeline import BehavioralChainRecord, NormalizedIntentRecord, ParserGraphEdge, SemanticBehaviorLayerResult, StructuredExtractionLayerResult
from models.pipeline import ControlLoopDefinition, DetectedTag, EngineeringEntity, InferredRelationship
from services.cross_validation_service import cross_validation_service
from services.entity_classification_service import entity_classification_service
from services.narrative_rule_extraction_service import narrative_rule_extraction_service
from services.process_unit_assignment_service import process_unit_assignment_service
from services.process_unit_detection_service import process_unit_detection_service
from services.semantic_normalization_service import semantic_normalization_service
from services.signal_classification import classify_behavioral_role, process_role_from_node, signal_type_from_tag


class SemanticBehaviorLayer:
    SENSOR_TYPES = {
        "analyzer",
        "flow_transmitter",
        "level_transmitter",
        "level_switch",
        "pressure_transmitter",
        "differential_pressure_transmitter",
        "temperature_transmitter",
    }
    ACTUATOR_TYPES = {"pump", "valve", "control_valve", "blower", "chemical_system_device", "motor", "vfd"}

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def process(self, structured: StructuredExtractionLayerResult) -> SemanticBehaviorLayerResult:
        self._structured_tag_metadata = self._tag_metadata(structured)
        detected_tags = [
            DetectedTag(
                normalized_tag=item.normalized_tag,
                raw_tag=item.raw_tag,
                family=item.family,
                canonical_type=item.canonical_type,
                source_file_id=item.source_file_id,
                source_file_name=item.source_file_name,
                source_page=item.source_page,
                source_text=item.source_text,
                confidence=item.confidence,
            )
            for item in structured.extracted_tags
        ]
        entities = entity_classification_service.build_entities(detected_tags)
        narrative_blob = "\n".join(block.text for block in structured.blocks if block.block_type == "narrative_section")
        entities = entity_classification_service.assign_process_units(entities, narrative_blob)

        process_units, synthetic_nodes = process_unit_detection_service.detect(
            pid_chunks=structured.pid_chunks,
            narrative_chunks=structured.narrative_chunks,
            entities=entities,
        )
        entities = self._append_process_nodes(entities, process_units, synthetic_nodes)
        entities, part_of_relationships, assignment_warnings = process_unit_assignment_service.assign(entities=entities, process_units=process_units)

        rule_bundle = narrative_rule_extraction_service.extract_rules(self._narrative_like_chunks(structured))
        semantic_intents = self._normalize_intents(structured, entities)
        candidate_relationships = self._build_candidate_relationships(structured, entities, semantic_intents)
        candidate_relationships.extend(part_of_relationships)
        supported_relationships, rejected_relationships, relationship_validation_debug = cross_validation_service.validate_relationships(
            candidate_relationships,
            entities,
            semantic_intents,
        )
        behavioral_chains = self._detect_behavioral_chains(supported_relationships, entities, semantic_intents)
        metadata_by_entity = self._build_metadata(entities, supported_relationships, semantic_intents, behavioral_chains)

        warnings = [*structured.warnings, *assignment_warnings]
        if not supported_relationships:
            warnings.append("Semantic layer rejected all candidate relationships after deterministic cross-validation.")

        self.logger.info(
            "Semantic behavior layer: entities=%s supported_relationships=%s rejected_relationships=%s intents=%s chains=%s",
            len(entities),
            len(supported_relationships),
            len(rejected_relationships),
            len(semantic_intents),
            len(behavioral_chains),
        )
        return SemanticBehaviorLayerResult(
            entities=sorted(entities, key=lambda item: item.id),
            process_units=sorted(process_units, key=lambda item: item.id),
            synthetic_nodes=sorted(synthetic_nodes, key=lambda item: item.id),
            semantic_intents=semantic_intents,
            normalized_intents=semantic_intents,
            behavioral_chains=behavioral_chains,
            supported_relationships=sorted(supported_relationships, key=lambda item: (item.source_entity, item.target_entity, item.relationship_type)),
            rejected_relationships=sorted(rejected_relationships, key=lambda item: (item.source_entity, item.target_entity, item.relationship_type)),
            relationship_validation_debug=relationship_validation_debug,
            metadata_by_entity=metadata_by_entity,
            rule_bundle=rule_bundle,
            warnings=warnings,
        )

    def _append_process_nodes(self, entities, process_units, synthetic_nodes):
        extended = list(entities)
        existing_ids = {entity.id for entity in extended}
        for unit in process_units:
            if unit.id in existing_ids:
                continue
            extended.append(
                EngineeringEntity(
                    id=unit.id,
                    tag=unit.id,
                    canonical_type="process_unit",
                    display_name=unit.name,
                    aliases=unit.aliases,
                    process_unit=unit.id,
                    source_documents=[],
                    source_pages=[],
                    source_snippets=[],
                    confidence=unit.confidence,
                    is_synthetic=True,
                    explanation=f"Process unit node ({unit.canonical_type})",
                    source_references=unit.source_references,
                    parse_notes=["Detected process unit node"],
                )
            )
            existing_ids.add(unit.id)

        for synthetic in synthetic_nodes:
            if synthetic.id in existing_ids:
                continue
            extended.append(
                EngineeringEntity(
                    id=synthetic.id,
                    tag=synthetic.id,
                    canonical_type=synthetic.canonical_type,
                    display_name=synthetic.label,
                    aliases=[],
                    process_unit=synthetic.process_unit,
                    source_documents=[],
                    source_pages=[],
                    source_snippets=[],
                    confidence=synthetic.confidence,
                    is_synthetic=True,
                    explanation=synthetic.explanation,
                    source_references=synthetic.source_references,
                    parse_notes=["Synthetic topology node"],
                )
            )
            existing_ids.add(synthetic.id)
        return extended

    def _normalize_intents(self, structured: StructuredExtractionLayerResult, entities: list[EngineeringEntity]) -> list[NormalizedIntentRecord]:
        entity_map = {entity.id: entity for entity in entities}
        normalized: list[NormalizedIntentRecord] = []

        for index, intent in enumerate(structured.extracted_control_intents, start=1):
            support = []
            if intent.source_text:
                support.append("document_text")
            if intent.source_tag and intent.target_tag and cross_validation_service._tag_pattern_support(intent.source_tag, intent.target_tag, intent.intent_type):
                support.append("tag_naming_pattern")
            if intent.source_tag in entity_map and intent.target_tag in entity_map:
                source_entity = entity_map[intent.source_tag]
                target_entity = entity_map[intent.target_tag]
                if source_entity.process_unit and source_entity.process_unit == target_entity.process_unit:
                    support.append("graph_topology")

            normalized_verb = semantic_normalization_service.normalize_verb(intent.source_text) or intent.normalized_verb or "controls"
            normalized.append(
                NormalizedIntentRecord(
                    intent_id=f"intent:{intent.source_block_id}:{index}",
                    intent_type=intent.intent_type,
                    normalized_verb=normalized_verb,
                    source_tag=intent.source_tag,
                    target_tag=intent.target_tag,
                    related_tags=intent.related_tags,
                    source_text=intent.source_text,
                    source_section_id=intent.source_section_id,
                    source_section_reference=intent.source_section_reference,
                    source_block_id=intent.source_block_id,
                    source_file_id=intent.source_file_id,
                    source_file_name=intent.source_file_name,
                    source_page=intent.source_page,
                    support=sorted(set(support)),
                    support_count=len(set(support)),
                    confidence=max(intent.confidence, 0.8 if len(set(support)) >= 2 else 0.68),
                )
            )

        return sorted(normalized, key=lambda item: (item.intent_type, item.source_page, item.intent_id))

    def _build_candidate_relationships(self, structured, entities, normalized_intents):
        entity_ids = {entity.id for entity in entities}
        candidates: dict[tuple[str, str, str], InferredRelationship] = {}

        for relationship in structured.merge_result.graph.edges:
            raw_relationship_type = self._preferred_raw_relationship_type(relationship)
            if relationship.source not in entity_ids or relationship.target not in entity_ids or raw_relationship_type is None:
                continue
            key = (relationship.source, relationship.target, raw_relationship_type)
            inference_source = "narrative" if relationship.raw_verbs else "merged"
            candidates[key] = InferredRelationship(
                relationship_type=raw_relationship_type,
                source_entity=relationship.source,
                target_entity=relationship.target,
                confidence_score=relationship.confidence_score,
                confidence_level=self._confidence_level(relationship.confidence_score),
                inference_source=inference_source,
                explanation=self._graph_edge_explanation(relationship),
                source_references=list(relationship.evidence_references),
            )

        for intent in normalized_intents:
            if intent.source_tag not in entity_ids or intent.target_tag not in entity_ids:
                continue
            key = (intent.source_tag, intent.target_tag, "CONTROLS")
            candidates[key] = InferredRelationship(
                relationship_type="CONTROLS",
                source_entity=str(intent.source_tag),
                target_entity=str(intent.target_tag),
                confidence_score=max(intent.confidence, 0.86),
                confidence_level=self._confidence_level(max(intent.confidence, 0.86)),
                inference_source="narrative",
                explanation=f"Normalized {intent.intent_type.replace('_', ' ')} intent from segmented document text.",
                source_references=[intent.source_text[:180]],
            )

        entity_map = {entity.id: entity for entity in entities}
        for entity in entities:
            if entity.id not in entity_map or entity.process_unit is None or entity.canonical_type == "process_unit":
                continue
            if entity.canonical_type in self.SENSOR_TYPES:
                key = (entity.id, entity.process_unit, "MEASURES")
                candidates[key] = InferredRelationship(
                    relationship_type="MEASURES",
                    source_entity=entity.id,
                    target_entity=entity.process_unit,
                    confidence_score=0.84,
                    confidence_level="HIGH",
                    inference_source="assignment",
                    explanation="Deterministic sensor-to-process measurement mapping from staged semantic layer.",
                    source_references=[f"process_unit:{entity.process_unit}"],
                )

        for loop in self._control_loop_relationships_from_rules(normalized_intents):
            key = (loop.source_entity, loop.target_entity, loop.relationship_type)
            candidates[key] = loop

        return list(candidates.values())

    @staticmethod
    def _preferred_raw_relationship_type(edge: ParserGraphEdge) -> str | None:
        if edge.raw_relationship_types:
            for preferred in ("CONTROLS", "MEASURES", "FEEDS", "PROCESS_FLOW", "CONNECTED_TO", "MONITORS", "SIGNAL_TO"):
                if preferred in edge.raw_relationship_types:
                    return preferred
            return edge.raw_relationship_types[0]
        mapping = {
            "control": "CONTROLS",
            "measurement": "MEASURES",
            "flow": "CONNECTED_TO",
        }
        return mapping.get(edge.relationship_type)

    @staticmethod
    def _graph_edge_explanation(edge: ParserGraphEdge) -> str:
        components = edge.confidence_factors
        return (
            f"Merged parser graph edge ({edge.relationship_type}) from extracted evidence. "
            f"Factors: text={components.direct_textual_evidence:.2f}, verb={components.verb_match_strength:.2f}, "
            f"tag_pattern={components.tag_pattern_compatibility:.2f}, topology={components.topology_consistency:.2f}."
        )

    def _detect_behavioral_chains(self, relationships, entities, intents):
        entity_map = {entity.id: entity for entity in entities}
        role_map = self._behavioral_role_map(entities)
        control_edges = [
            rel
            for rel in relationships
            if rel.relationship_type in {"CONTROLS", "SIGNAL_TO"}
            and role_map.get(rel.source_entity, {}).get("role") == "sensor"
            and role_map.get(rel.target_entity, {}).get("role") == "actuator"
        ]
        chains: dict[tuple[str, str, str], BehavioralChainRecord] = {}
        intent_map: dict[tuple[str, str], list[NormalizedIntentRecord]] = defaultdict(list)
        measurement_map: dict[str, list[InferredRelationship]] = defaultdict(list)
        impact_map: dict[str, list[InferredRelationship]] = defaultdict(list)
        for intent in intents:
            if intent.source_tag and intent.target_tag:
                intent_map[(intent.source_tag, intent.target_tag)].append(intent)

        for relationship in relationships:
            if relationship.relationship_type in {"MEASURES", "MONITORS"}:
                measurement_map[relationship.source_entity].append(relationship)
            if relationship.relationship_type in {"PART_OF", "PROCESS_FLOW", "FEEDS", "DISCHARGES_TO", "CONNECTED_TO", "CONTROLS", "SUPPLIES_AIR_TO"}:
                impact_map[relationship.source_entity].append(relationship)

        for relationship in control_edges:
            sensor = entity_map.get(relationship.source_entity)
            actuator = entity_map.get(relationship.target_entity)
            if sensor is None or actuator is None:
                continue
            sensor_role = role_map.get(sensor.id, {})
            actuator_role = role_map.get(actuator.id, {})
            if sensor_role.get("role") != "sensor" or actuator_role.get("role") != "actuator":
                continue

            process_candidates: dict[str, dict[str, object]] = {}

            def add_process_candidate(process_id: str | None, evidence: str, confidence: float) -> None:
                if not process_id:
                    return
                process_key = str(process_id)
                current = process_candidates.get(process_key)
                if current is None:
                    process_candidates[process_key] = {"evidence": [evidence], "confidence": confidence}
                    return
                if evidence not in current["evidence"]:
                    current["evidence"].append(evidence)
                current["confidence"] = max(float(current["confidence"]), confidence)

            for measure_edge in measurement_map.get(sensor.id, []):
                target_role = role_map.get(measure_edge.target_entity, {}).get("role")
                if target_role == "process":
                    add_process_candidate(
                        measure_edge.target_entity,
                        f"measurement_edge:{measure_edge.source_entity}->{measure_edge.target_entity}",
                        measure_edge.confidence_score,
                    )

            for impact_edge in impact_map.get(actuator.id, []):
                target_role = role_map.get(impact_edge.target_entity, {}).get("role")
                if target_role == "process":
                    add_process_candidate(
                        impact_edge.target_entity,
                        f"impact_edge:{impact_edge.relationship_type}:{impact_edge.source_entity}->{impact_edge.target_entity}",
                        impact_edge.confidence_score,
                    )

            if sensor.process_unit:
                add_process_candidate(sensor.process_unit, f"sensor_process_unit:{sensor.process_unit}", 0.82)
            if actuator.process_unit:
                add_process_candidate(actuator.process_unit, f"actuator_process_unit:{actuator.process_unit}", 0.84)

            if not process_candidates:
                continue

            related_intents = intent_map.get((sensor.id, actuator.id), [])
            source_texts = []
            if related_intents:
                source_texts.extend([intent.source_text for intent in related_intents if intent.source_text])
            inferred_intent = related_intents[0].intent_type if related_intents else self._infer_intent_from_entity(sensor)

            for process_node, process_data in process_candidates.items():
                support = {"graph_topology"}
                process_role = role_map.get(process_node, {})
                evidence = [
                    f"control_edge:{sensor.id}->{actuator.id}",
                    *sensor_role.get("evidence", []),
                    *actuator_role.get("evidence", []),
                    *process_role.get("evidence", []),
                    *[str(item) for item in process_data.get("evidence", [])],
                ]
                if related_intents:
                    support.add("document_text")
                    evidence.extend([f"intent:{intent.source_text[:160]}" for intent in related_intents if intent.source_text])
                if inferred_intent and cross_validation_service._tag_pattern_support(sensor.id, actuator.id, inferred_intent):
                    support.add("tag_naming_pattern")
                    evidence.append(f"tag_pair:{sensor.id}:{actuator.id}")

                if len(support) < 2:
                    continue

                confidence_components = [
                    relationship.confidence_score,
                    float(sensor_role.get("confidence", sensor.confidence)),
                    float(actuator_role.get("confidence", actuator.confidence)),
                    float(process_data.get("confidence", 0.78)),
                ]
                if process_role:
                    confidence_components.append(float(process_role.get("confidence", 0.8)))
                if related_intents:
                    confidence_components.append(max(intent.confidence for intent in related_intents))

                key = (sensor.id, actuator.id, process_node)
                chains[key] = BehavioralChainRecord(
                    chain_id=f"chain:{sensor.id}:{actuator.id}:{process_node}",
                    sensor=sensor.id,
                    actuator=actuator.id,
                    process=process_node,
                    chain=[sensor.id, actuator.id, process_node],
                    evidence=sorted({item for item in evidence if item}),
                    intent_type=inferred_intent,
                    source_texts=sorted({text for text in source_texts if text}),
                    support=sorted(support),
                    support_count=len(support),
                    confidence=min(0.99, (sum(confidence_components) / len(confidence_components)) + 0.03 * len(support)),
                )
        return sorted(chains.values(), key=lambda item: (item.process, item.sensor, item.actuator))

    def _behavioral_role_map(self, entities):
        structured_tag_metadata = getattr(self, "_structured_tag_metadata", {})
        role_map: dict[str, dict[str, object]] = {}
        for entity in entities:
            extracted_metadata = structured_tag_metadata.get(entity.id, {})
            role, evidence, confidence = classify_behavioral_role(
                entity.id,
                node_type=entity.canonical_type,
                normalized_equipment=str(extracted_metadata.get("normalized_equipment") or ""),
                normalized_type=str(extracted_metadata.get("normalized_type") or entity.canonical_type),
            )
            role_map[entity.id] = {
                "role": role,
                "evidence": evidence,
                "confidence": confidence,
            }
        return role_map

    def _build_metadata(self, entities, relationships, intents, chains):
        metadata: dict[str, dict[str, object]] = {}
        chains_by_entity: dict[str, list[str]] = defaultdict(list)
        structured_tag_metadata = getattr(self, "_structured_tag_metadata", {})
        role_map = self._behavioral_role_map(entities)
        for chain in chains:
            chain_string = "->".join(chain.chain or [chain.sensor, chain.actuator, chain.process])
            for entity_id in {chain.sensor, chain.actuator, chain.process}:
                chains_by_entity[entity_id].append(chain_string)

        intents_by_source: dict[str, list[str]] = defaultdict(list)
        for intent in intents:
            if intent.source_tag:
                intents_by_source[intent.source_tag].append(intent.intent_type)

        outgoing: dict[str, list[InferredRelationship]] = defaultdict(list)
        for relationship in relationships:
            outgoing[relationship.source_entity].append(relationship)

        for entity in entities:
            extracted_metadata = structured_tag_metadata.get(entity.id, {})
            normalized_type = str(extracted_metadata.get("normalized_type") or entity.canonical_type)
            normalized_equipment = str(extracted_metadata.get("normalized_equipment") or normalized_type)
            matched_pattern = extracted_metadata.get("matched_pattern")
            role_info = role_map.get(entity.id, {})
            entry: dict[str, object] = {
                "equipment_type": normalized_equipment,
                "normalized_type": normalized_type,
                "signal_type": signal_type_from_tag(entity.id, entity.canonical_type),
                "control_role": str(role_info.get("role") or process_role_from_node(entity.canonical_type)),
                "behavioral_role_evidence": list(role_info.get("evidence", [])),
                "behavioral_role_confidence": float(role_info.get("confidence", 0.7)),
                "process_unit": entity.process_unit or "unassigned",
                "controls": sorted({rel.target_entity for rel in outgoing.get(entity.id, []) if rel.relationship_type in {"CONTROLS", "SIGNAL_TO"}}),
                "measures": sorted({rel.target_entity for rel in outgoing.get(entity.id, []) if rel.relationship_type == "MEASURES"}),
                "behavioral_chains": sorted(set(chains_by_entity.get(entity.id, []))),
                "detected_intents": sorted(set(intents_by_source.get(entity.id, []))),
                "metadata_confidence": {
                    "equipment_type": 0.9,
                    "normalized_type": 0.95,
                    "signal_type": 0.85,
                    "control_role": float(role_info.get("confidence", 0.85)),
                    "process_unit": 0.84 if entity.process_unit else 0.4,
                },
            }
            if matched_pattern:
                entry["matched_pattern"] = str(matched_pattern)
            if entry["signal_type"] == "analog":
                entry["instrument_role"] = "measurement"
            elif entity.canonical_type == "level_switch":
                entry["instrument_role"] = "switch"
            metadata[entity.id] = entry
        return metadata

    @staticmethod
    def _tag_metadata(structured: StructuredExtractionLayerResult) -> dict[str, dict[str, object]]:
        metadata: dict[str, dict[str, object]] = {}
        for item in structured.extracted_tags:
            existing = metadata.get(item.normalized_tag)
            payload = {
                "normalized_equipment": item.normalized_equipment,
                "normalized_type": item.normalized_type,
                "matched_pattern": item.matched_pattern,
                "confidence": item.confidence,
            }
            if existing is None or float(payload["confidence"]) >= float(existing.get("confidence", 0.0)):
                metadata[item.normalized_tag] = payload
        return metadata

    def _narrative_like_chunks(self, structured: StructuredExtractionLayerResult):
        return [
            chunk.model_copy(update={"text": block.text, "section": block.section})
            for block in structured.blocks
            if block.block_type == "narrative_section"
            for chunk in [next((item for item in structured.narrative_chunks if item.file_id == block.file_id and item.page_number == block.page_number), structured.narrative_chunks[0] if structured.narrative_chunks else None)]
            if chunk is not None
        ]

    @staticmethod
    def _control_loop_relationships_from_rules(intents):
        relationships: list[InferredRelationship] = []
        for intent in intents:
            if not intent.source_tag or not intent.target_tag:
                continue
            relationships.append(
                InferredRelationship(
                    relationship_type="CONTROLS",
                    source_entity=intent.source_tag,
                    target_entity=intent.target_tag,
                    confidence_score=max(intent.confidence, 0.88),
                    confidence_level="HIGH",
                    inference_source="narrative",
                    explanation=f"Normalized {intent.intent_type.replace('_', ' ')} control intent.",
                    source_references=[intent.source_text],
                )
            )
        return relationships

    @staticmethod
    def _confidence_level(confidence: float) -> str:
        if confidence >= 0.85:
            return "HIGH"
        if confidence >= 0.6:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _infer_intent_from_entity(entity):
        mapping = {
            "flow_transmitter": "flow_control",
            "level_transmitter": "level_control",
            "level_switch": "level_control",
            "pressure_transmitter": "pressure_control",
            "differential_pressure_transmitter": "pressure_control",
            "temperature_transmitter": "temperature_control",
        }
        return mapping.get(entity.canonical_type)

semantic_behavior_layer = SemanticBehaviorLayer()
