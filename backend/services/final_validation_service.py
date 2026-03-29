from __future__ import annotations

import logging
from collections import defaultdict, deque

from models.document_pipeline import (
    FinalValidationDiagnostics,
    FinalValidationLayerResult,
    PipelineControlLoopRecord,
    TuningDataRecord,
    ValidatedGraphRecord,
)
from models.engineering_table import EngineeringTableRow
from models.pipeline import EngineeringEntity, InferredRelationship
from services.engineering_table_parser import engineering_table_parser
from services.graph_build_service import graph_build_service
from services.graph_validation_service import graph_validation_service
from services.parser_relationship_graph_service import parser_relationship_graph_service
from services.signal_classification import process_role_from_node


class FinalValidationService:
    INVALID_EQUIPMENT_VALUES = {"", "unknown", "generic_equipment", "generic_device", None}
    DIRECTIONAL_RELATIONSHIP_TYPES = {"PROCESS_FLOW", "FEEDS", "DISCHARGES_TO", "SUPPLIES_AIR_TO", "MEASURES", "CONTROLS", "SIGNAL_TO", "MONITORS", "PART_OF"}

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def process(self, structured, semantic, validation) -> FinalValidationLayerResult:
        diagnostics = FinalValidationDiagnostics(
            total_tags=len(semantic.entities),
            total_relationships=len(validation.validated_graph.relationships) + len(validation.low_confidence_relationships),
            total_loops=len(validation.control_loops) + len(validation.rejected_control_loops),
        )
        warnings: list[str] = []

        relationships, duplicate_edge_rejects, duplicate_edges_removed = self._deduplicate_relationships(validation.validated_graph.relationships)
        contradiction_kept, contradiction_rejects = self._reject_contradictions(semantic.entities, relationships)
        diagnostics.duplicate_edges_removed = duplicate_edges_removed

        preliminary_rejected_relationships = [
            *validation.low_confidence_relationships,
            *duplicate_edge_rejects,
            *contradiction_rejects,
        ]

        loop_candidates, loop_duplicate_rejects, duplicate_loops_removed = self._deduplicate_loops(validation.control_loops)
        diagnostics.duplicate_loops_removed = duplicate_loops_removed

        tag_rows, rejected_tag_rows = self._build_and_validate_tag_rows(
            entities=semantic.entities,
            relationships=contradiction_kept,
            control_loops=loop_candidates,
            metadata_by_entity=semantic.metadata_by_entity,
            behavioral_chains=semantic.behavioral_chains,
            structured=structured,
        )
        valid_tags = {row.tag for row in tag_rows}
        filtered_entities = [entity for entity in semantic.entities if entity.id in valid_tags]

        final_relationships, connectivity_rejects = self._filter_relationships_to_valid_tags(contradiction_kept, valid_tags)
        final_rejected_relationships = self._merge_relationship_rejections(preliminary_rejected_relationships, connectivity_rejects)

        valid_rows_by_tag = {row.tag: row for row in tag_rows}
        final_loops, invalid_loop_rejects = self._validate_loops(loop_candidates, valid_rows_by_tag, final_relationships)
        final_rejected_loops = self._merge_rejected_loops(validation.rejected_control_loops, [*loop_duplicate_rejects, *invalid_loop_rejects])

        retained_loop_ids = {loop.loop_id for loop in final_loops}
        final_tuning_data = [item for item in validation.tuning_data if item.loop_reference in retained_loop_ids]

        final_tag_rows, additional_rejected_rows = self._build_and_validate_tag_rows(
            entities=filtered_entities,
            relationships=final_relationships,
            control_loops=final_loops,
            metadata_by_entity=semantic.metadata_by_entity,
            behavioral_chains=semantic.behavioral_chains,
            structured=structured,
        )
        if additional_rejected_rows:
            additional_invalid_tags = {row.tag for row in additional_rejected_rows}
            filtered_entities = [entity for entity in filtered_entities if entity.id not in additional_invalid_tags]
            final_relationships, extra_connectivity_rejects = self._filter_relationships_to_valid_tags(final_relationships, {row.tag for row in final_tag_rows})
            final_rejected_relationships = self._merge_relationship_rejections(final_rejected_relationships, extra_connectivity_rejects)
            final_loops, secondary_invalid_loop_rejects = self._validate_loops(final_loops, {row.tag: row for row in final_tag_rows}, final_relationships)
            final_rejected_loops = self._merge_rejected_loops(final_rejected_loops, secondary_invalid_loop_rejects)
            retained_loop_ids = {loop.loop_id for loop in final_loops}
            final_tuning_data = [item for item in final_tuning_data if item.loop_reference in retained_loop_ids]
            rejected_tag_rows = [*rejected_tag_rows, *additional_rejected_rows]

        if not final_tag_rows and semantic.entities:
            raise ValueError("Final validation rejected all deterministic tag rows; refusing to return invalid response objects.")

        parser_graph = parser_relationship_graph_service.build_from_validated_relationships(
            filtered_entities,
            final_relationships,
            metadata_by_entity=semantic.metadata_by_entity,
        )
        final_graph = ValidatedGraphRecord(
            entities=filtered_entities,
            relationships=final_relationships,
            rejected_relationships=final_rejected_relationships,
            parser_graph=parser_graph,
            warnings=[*validation.validated_graph.warnings, *parser_graph.warnings],
        )

        diagnostics.rejected_tags = len({row.tag for row in rejected_tag_rows})
        diagnostics.rejected_relationships = len(final_rejected_relationships)
        diagnostics.rejected_loops = len(final_rejected_loops)
        diagnostics.inferred_links = self._count_inferred_links(final_tag_rows)

        if parser_graph.contradictions:
            warnings.extend(item.message for item in parser_graph.contradictions)
        if rejected_tag_rows:
            warnings.append(f"Final validator rejected {len(rejected_tag_rows)} invalid tag rows before API serialization.")
        if duplicate_edges_removed:
            warnings.append(f"Final validator removed {duplicate_edges_removed} duplicate graph edges.")
        if duplicate_loops_removed:
            warnings.append(f"Final validator removed {duplicate_loops_removed} duplicate control loops.")
        if invalid_loop_rejects:
            warnings.append(f"Final validator rejected {len(invalid_loop_rejects)} inconsistent control loops.")

        self.logger.info(
            "Final validation: tag_rows=%s rejected_tags=%s relationships=%s rejected_relationships=%s loops=%s rejected_loops=%s inferred_links=%s",
            len(final_tag_rows),
            diagnostics.rejected_tags,
            len(final_relationships),
            diagnostics.rejected_relationships,
            len(final_loops),
            diagnostics.rejected_loops,
            diagnostics.inferred_links,
        )
        return FinalValidationLayerResult(
            validated_graph=final_graph,
            tag_rows=final_tag_rows,
            rejected_tag_rows=sorted(rejected_tag_rows, key=lambda item: item.tag),
            control_loops=sorted(final_loops, key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node)),
            rejected_control_loops=final_rejected_loops,
            tuning_data=sorted(final_tuning_data, key=lambda item: (item.loop_reference or "", item.source_page, item.tuning_id)),
            diagnostics=diagnostics,
            warnings=warnings,
        )

    def _deduplicate_relationships(
        self,
        relationships: list[InferredRelationship],
    ) -> tuple[list[InferredRelationship], list[InferredRelationship], int]:
        kept_by_key: dict[tuple[str, str, str], InferredRelationship] = {}
        rejected: list[InferredRelationship] = []
        duplicate_count = 0
        for relationship in relationships:
            key = (relationship.source_entity, relationship.target_entity, relationship.relationship_type)
            current = kept_by_key.get(key)
            if current is None:
                kept_by_key[key] = relationship
                continue
            duplicate_count += 1
            if self._relationship_sort_key(relationship) < self._relationship_sort_key(current):
                rejected.append(current)
                kept_by_key[key] = relationship
            else:
                rejected.append(relationship)
        ordered = sorted(kept_by_key.values(), key=lambda item: (item.source_entity, item.target_entity, item.relationship_type, -item.confidence_score))
        return ordered, sorted(rejected, key=lambda item: (item.source_entity, item.target_entity, item.relationship_type)), duplicate_count

    def _reject_contradictions(
        self,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
    ) -> tuple[list[InferredRelationship], list[InferredRelationship]]:
        entity_map = {entity.id: entity for entity in entities}
        by_pair: dict[tuple[str, str], list[InferredRelationship]] = defaultdict(list)
        by_directed_type: dict[tuple[str, str, str], InferredRelationship] = {
            (item.source_entity, item.target_entity, item.relationship_type): item for item in relationships
        }

        for item in relationships:
            by_pair[(item.source_entity, item.target_entity)].append(item)

        rejected_ids: set[int] = set()
        kept: list[InferredRelationship] = []
        rejected: list[InferredRelationship] = []

        for pair, pair_items in by_pair.items():
            if len(pair_items) > 1:
                winner = min(pair_items, key=self._relationship_sort_key)
                for item in pair_items:
                    if item is winner:
                        continue
                    rejected_ids.add(id(item))

        seen_bidirectional: set[tuple[str, str, str]] = set()
        for item in relationships:
            if item.relationship_type not in self.DIRECTIONAL_RELATIONSHIP_TYPES:
                continue
            reverse_key = (item.target_entity, item.source_entity, item.relationship_type)
            reverse = by_directed_type.get(reverse_key)
            if reverse is None:
                continue
            normalized_pair = tuple(sorted([item.source_entity, item.target_entity])) + (item.relationship_type,)
            if normalized_pair in seen_bidirectional:
                continue
            seen_bidirectional.add(normalized_pair)
            winner = self._preferred_direction(item, reverse, entity_map)
            loser = reverse if winner is item else item
            rejected_ids.add(id(loser))

        for item in relationships:
            if id(item) in rejected_ids:
                rejected.append(item)
            else:
                kept.append(item)

        return (
            sorted(kept, key=lambda rel: (rel.source_entity, rel.target_entity, rel.relationship_type)),
            sorted(rejected, key=lambda rel: (rel.source_entity, rel.target_entity, rel.relationship_type)),
        )

    def _build_and_validate_tag_rows(
        self,
        *,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
        control_loops: list[PipelineControlLoopRecord],
        metadata_by_entity: dict[str, dict[str, object]],
        behavioral_chains,
        structured,
    ) -> tuple[list[EngineeringTableRow], list[EngineeringTableRow]]:
        entity_payloads = self._entity_payloads(entities, metadata_by_entity)
        relationship_map = self._relationship_map(relationships)
        loop_index = self._loop_index(control_loops)
        metadata_rows = self._context_metadata_rows(structured)
        updown = engineering_table_parser._upstream_downstream_calculation(
            entities=entity_payloads,
            relationships=relationship_map,
            loops=loop_index,
            behavioral_chains=behavioral_chains,
            metadata_rows=metadata_rows,
            max_depth=4,
        )
        context = self._context_map(entity_payloads)
        metadata = engineering_table_parser._engineering_metadata_extraction(entity_payloads)
        traceability = engineering_table_parser._traceability_mapping(entity_payloads, context, relationship_map)
        derived = engineering_table_parser._derived_field_generation(entity_payloads, relationship_map, loop_index, updown)
        rows = engineering_table_parser._row_building(
            entities=entity_payloads,
            context=context,
            relationships=relationship_map,
            loops=loop_index,
            updown=updown,
            metadata=metadata,
            traceability=traceability,
            derived=derived,
            include_inferred=True,
        )
        engineering_table_parser._confidence_scoring(rows)
        engineering_table_parser._annotate_row_warnings(rows)

        valid: list[EngineeringTableRow] = []
        rejected: list[EngineeringTableRow] = []
        for row in rows:
            invalid_reasons = self._invalid_row_reasons(row)
            if invalid_reasons:
                rejected.append(row.model_copy(update={"warnings": sorted(set([*row.warnings, *invalid_reasons]))}))
            else:
                valid.append(row)
        return sorted(valid, key=lambda item: item.tag), sorted(rejected, key=lambda item: item.tag)

    @staticmethod
    def _filter_relationships_to_valid_tags(
        relationships: list[InferredRelationship],
        valid_tags: set[str],
    ) -> tuple[list[InferredRelationship], list[InferredRelationship]]:
        kept: list[InferredRelationship] = []
        rejected: list[InferredRelationship] = []
        for relationship in relationships:
            if relationship.source_entity in valid_tags and relationship.target_entity in valid_tags:
                kept.append(relationship)
            else:
                rejected.append(relationship)
        return kept, rejected

    def _deduplicate_loops(
        self,
        control_loops: list[PipelineControlLoopRecord],
    ) -> tuple[list[PipelineControlLoopRecord], list[PipelineControlLoopRecord], int]:
        kept: dict[tuple[str, str, str], PipelineControlLoopRecord] = {}
        rejected: list[PipelineControlLoopRecord] = []
        duplicate_count = 0
        for loop in control_loops:
            key = (loop.sensor_tag, loop.actuator_tag, loop.process_node)
            current = kept.get(key)
            if current is None:
                kept[key] = loop
                continue
            duplicate_count += 1
            if self._loop_sort_key(loop) < self._loop_sort_key(current):
                rejected.append(current)
                kept[key] = loop
            else:
                rejected.append(loop)
        return (
            sorted(kept.values(), key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node)),
            sorted(rejected, key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node)),
            duplicate_count,
        )

    def _validate_loops(
        self,
        loops: list[PipelineControlLoopRecord],
        rows_by_tag: dict[str, EngineeringTableRow],
        relationships: list[InferredRelationship],
    ) -> tuple[list[PipelineControlLoopRecord], list[PipelineControlLoopRecord]]:
        relationship_keys = {(item.source_entity, item.target_entity, item.relationship_type) for item in relationships}
        kept: list[PipelineControlLoopRecord] = []
        rejected: list[PipelineControlLoopRecord] = []
        for loop in loops:
            reasons = self._invalid_loop_reasons(loop, rows_by_tag, relationship_keys)
            if reasons:
                rejected.append(loop.model_copy(update={"tuning": {**dict(loop.tuning), "validation_errors": reasons}}))
            else:
                kept.append(loop)
        return kept, sorted(rejected, key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node))

    @staticmethod
    def _merge_rejected_loops(
        existing: list[PipelineControlLoopRecord],
        incoming: list[PipelineControlLoopRecord],
    ) -> list[PipelineControlLoopRecord]:
        merged: dict[str, PipelineControlLoopRecord] = {}
        for item in [*existing, *incoming]:
            current = merged.get(item.loop_id)
            if current is None or item.confidence >= current.confidence:
                merged[item.loop_id] = item
        return sorted(merged.values(), key=lambda item: (-item.confidence, item.sensor_tag, item.actuator_tag, item.process_node))

    @staticmethod
    def _merge_relationship_rejections(
        existing: list[InferredRelationship],
        incoming: list[InferredRelationship],
    ) -> list[InferredRelationship]:
        merged: dict[tuple[str, str, str], InferredRelationship] = {}
        for relationship in [*existing, *incoming]:
            key = (relationship.source_entity, relationship.target_entity, relationship.relationship_type)
            current = merged.get(key)
            if current is None or relationship.confidence_score >= current.confidence_score:
                merged[key] = relationship
        return sorted(merged.values(), key=lambda item: (item.source_entity, item.target_entity, item.relationship_type))

    def _entity_payloads(
        self,
        entities: list[EngineeringEntity],
        metadata_by_entity: dict[str, dict[str, object]],
    ) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for entity in sorted(entities, key=lambda item: item.id):
            metadata = dict(metadata_by_entity.get(entity.id, {}) or {})
            normalized_type = str(metadata.get("normalized_type") or entity.canonical_type)
            equipment = str(metadata.get("equipment_type") or metadata.get("normalized_equipment") or normalized_type)
            payloads.append(
                {
                    "id": entity.id,
                    "tag": entity.id,
                    "type": normalized_type,
                    "subtype": entity.canonical_type,
                    "description": entity.display_name,
                    "system": entity.process_unit,
                    "equipment": equipment,
                    "process_role": process_role_from_node(normalized_type),
                    "status": None,
                    "mode": metadata.get("mode"),
                    "power": metadata.get("power"),
                    "metadata": metadata,
                    "is_synthetic": bool(entity.is_synthetic),
                    "source_documents": list(entity.source_documents),
                    "source_references": list(entity.source_references),
                    "node_confidence": float(entity.confidence or 0.0),
                }
            )
        return payloads

    @staticmethod
    def _relationship_map(relationships: list[InferredRelationship]) -> dict[str, dict[str, set[str]]]:
        relation_map: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for relationship in relationships:
            source = relationship.source_entity
            target = relationship.target_entity
            relation_map[source]["connections"].add(target)
            relation_map[target]["connections"].add(source)

            if relationship.relationship_type in {"MEASURES", "MONITORS"}:
                relation_map[source]["measures"].add(target)
                relation_map[target]["signal_inputs"].add(source)
            if relationship.relationship_type in {"CONTROLS", "SIGNAL_TO"}:
                relation_map[source]["controls"].add(target)
                relation_map[target]["controlled_by"].add(source)
                relation_map[source]["signal_outputs"].add(target)
                relation_map[target]["signal_inputs"].add(source)
            if relationship.relationship_type in {"PROCESS_FLOW", "FEEDS", "DISCHARGES_TO", "SUPPLIES_AIR_TO", "PART_OF", "CONNECTED_TO"}:
                relation_map[source]["downstream"].add(target)
                relation_map[target]["upstream"].add(source)
        return relation_map

    @staticmethod
    def _loop_index(control_loops: list[PipelineControlLoopRecord]) -> dict[str, list[str]]:
        indexed: dict[str, list[str]] = defaultdict(list)
        for loop in control_loops:
            chain_value = "->".join([item for item in loop.chain if item])
            for tag in {loop.sensor_tag, loop.controller_tag, loop.actuator_tag, loop.process_node}:
                if tag:
                    indexed[tag].append(chain_value)
        return {tag: sorted(set(values)) for tag, values in indexed.items()}

    @staticmethod
    def _context_metadata_rows(structured) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for relationship in structured.extracted_relationships:
            rows.append(
                {
                    "category": "extracted_relationship",
                    "tag": relationship.source_tag,
                    "payload": relationship.model_dump(),
                }
            )
        return rows

    @staticmethod
    def _context_map(entities: list[dict[str, object]]) -> dict[str, dict[str, object]]:
        context: dict[str, dict[str, object]] = {}
        for entity in entities:
            tag = str(entity["tag"])
            context[tag] = {
                "document_source": sorted(set(str(item) for item in entity.get("source_documents", []) if item)),
                "line_reference": sorted(set(str(item) for item in entity.get("source_references", []) if item)),
                "metadata_matches": [],
            }
        return context

    def _invalid_row_reasons(self, row: EngineeringTableRow) -> list[str]:
        reasons: list[str] = []
        if not row.upstream or not row.downstream:
            reasons.append("missing_upstream_or_downstream")
        if not row.type or row.type == "unknown":
            reasons.append("unclassified_tag_type")
        if not row.process_role or row.process_role in {"unknown", "equipment", ""}:
            reasons.append("unclassified_process_role")
        if row.equipment in self.INVALID_EQUIPMENT_VALUES:
            reasons.append("unnormalized_equipment")
        if row.num_connections <= 0 and not row.control_chain:
            reasons.append("graph_disconnected")
        return reasons

    def _invalid_loop_reasons(
        self,
        loop: PipelineControlLoopRecord,
        rows_by_tag: dict[str, EngineeringTableRow],
        relationship_keys: set[tuple[str, str, str]],
    ) -> list[str]:
        reasons: list[str] = []
        required = [loop.sensor_tag, loop.actuator_tag, loop.process_node]
        if any(not item for item in required):
            reasons.append("missing_required_loop_roles")
        chain = [item for item in loop.chain if item]
        if len(chain) < 3:
            reasons.append("incomplete_loop_chain")
        if len(set(chain)) != len(chain):
            reasons.append("duplicate_nodes_in_loop_chain")
        for tag in [loop.sensor_tag, loop.controller_tag, loop.actuator_tag, loop.process_node]:
            if tag and tag not in rows_by_tag:
                reasons.append(f"missing_validated_tag:{tag}")
        sensor_row = rows_by_tag.get(loop.sensor_tag)
        actuator_row = rows_by_tag.get(loop.actuator_tag)
        process_row = rows_by_tag.get(loop.process_node)
        controller_row = rows_by_tag.get(loop.controller_tag) if loop.controller_tag else None
        if sensor_row and sensor_row.process_role != "sensor":
            reasons.append("sensor_role_mismatch")
        if actuator_row and actuator_row.process_role != "actuator":
            reasons.append("actuator_role_mismatch")
        if process_row and process_row.process_role != "process":
            reasons.append("process_role_mismatch")
        if controller_row and controller_row.process_role != "controller":
            reasons.append("controller_role_mismatch")
        if chain:
            if chain[0] != loop.sensor_tag:
                reasons.append("chain_sensor_mismatch")
            if chain[-1] != loop.process_node:
                reasons.append("chain_process_mismatch")
            if len(chain) >= 2 and chain[-2] != loop.actuator_tag:
                reasons.append("chain_actuator_mismatch")
            if loop.controller_tag and len(chain) >= 4 and chain[1] != loop.controller_tag:
                reasons.append("chain_controller_mismatch")
        if (loop.sensor_tag, loop.process_node, "MEASURES") not in relationship_keys and (loop.sensor_tag, loop.process_node, "MONITORS") not in relationship_keys:
            reasons.append("sensor_process_measurement_missing")
        control_edge_pairs = {(loop.sensor_tag, loop.controller_tag, "SIGNAL_TO"), (loop.sensor_tag, loop.controller_tag, "CONTROLS")} if loop.controller_tag else set()
        if loop.controller_tag and not any(edge in relationship_keys for edge in control_edge_pairs):
            reasons.append("sensor_controller_edge_missing")
        if loop.controller_tag and (loop.controller_tag, loop.actuator_tag, "CONTROLS") not in relationship_keys and (loop.controller_tag, loop.actuator_tag, "SIGNAL_TO") not in relationship_keys:
            reasons.append("controller_actuator_edge_missing")
        if not loop.controller_tag and (loop.sensor_tag, loop.actuator_tag, "CONTROLS") not in relationship_keys and (loop.sensor_tag, loop.actuator_tag, "SIGNAL_TO") not in relationship_keys:
            reasons.append("sensor_actuator_edge_missing")
        process_edge_pairs = {
            (loop.actuator_tag, loop.process_node, "PART_OF"),
            (loop.actuator_tag, loop.process_node, "PROCESS_FLOW"),
            (loop.actuator_tag, loop.process_node, "FEEDS"),
            (loop.actuator_tag, loop.process_node, "DISCHARGES_TO"),
            (loop.actuator_tag, loop.process_node, "CONNECTED_TO"),
            (loop.actuator_tag, loop.process_node, "SUPPLIES_AIR_TO"),
            (loop.actuator_tag, loop.process_node, "CONTROLS"),
        }
        if not any(edge in relationship_keys for edge in process_edge_pairs):
            reasons.append("actuator_process_edge_missing")
        return sorted(set(reasons))

    @staticmethod
    def _count_inferred_links(rows: list[EngineeringTableRow]) -> int:
        total = 0
        for row in rows:
            total += sum(1 for item in row.upstream_links if item.inferred)
            total += sum(1 for item in row.downstream_links if item.inferred)
        return total

    @staticmethod
    def _loop_sort_key(loop: PipelineControlLoopRecord) -> tuple[object, ...]:
        return (-float(loop.confidence), -float(loop.validation_score), -float(loop.continuity_score), loop.loop_id)

    @staticmethod
    def _relationship_sort_key(relationship: InferredRelationship) -> tuple[object, ...]:
        return (
            graph_validation_service._relationship_priority(relationship),
            graph_validation_service._inference_priority(relationship.inference_source),
            -float(relationship.confidence_score),
            relationship.source_entity,
            relationship.target_entity,
            relationship.relationship_type,
        )

    def _preferred_direction(
        self,
        left: InferredRelationship,
        right: InferredRelationship,
        entity_map: dict[str, EngineeringEntity],
    ) -> InferredRelationship:
        if left.relationship_type in {"MEASURES", "MONITORS"}:
            left_source_role = process_role_from_node(entity_map.get(left.source_entity).canonical_type if entity_map.get(left.source_entity) else None)
            left_target_role = process_role_from_node(entity_map.get(left.target_entity).canonical_type if entity_map.get(left.target_entity) else None)
            right_source_role = process_role_from_node(entity_map.get(right.source_entity).canonical_type if entity_map.get(right.source_entity) else None)
            right_target_role = process_role_from_node(entity_map.get(right.target_entity).canonical_type if entity_map.get(right.target_entity) else None)
            if left_source_role == "sensor" and left_target_role == "process":
                return left
            if right_source_role == "sensor" and right_target_role == "process":
                return right
        return left if self._relationship_sort_key(left) <= self._relationship_sort_key(right) else right


final_validation_service = FinalValidationService()