from __future__ import annotations

import logging
from collections import defaultdict

from models.pipeline import EngineeringEntity, GraphWarning, InferredRelationship


class GraphValidationService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.max_outgoing_edges = 3

        # Strict engineering compatibility matrix.
        self.compatibility_matrix: dict[str, set[str]] = {
            "pump": {"basin", "tank", "clarifier"},
            "blower": {"air_header", "basin"},
            "flow_transmitter": {"pipe", "valve", "pump"},
            "level_transmitter": {"tank", "wet_well"},
            "analyzer": {"control_valve", "basin"},
            "control_valve": {"pipe", "basin"},
        }

        self.sensor_types = {
            "analyzer",
            "flow_transmitter",
            "level_transmitter",
            "pressure_transmitter",
            "differential_pressure_transmitter",
            "level_switch",
        }

    @staticmethod
    def _inference_priority(inference_source: str | None) -> int:
        # Lower value means stronger preference.
        priority = {
            "narrative": 0,
            "merged": 1,
            "refinement": 2,
            "assignment": 3,
            "heuristic": 4,
            "locality": 5,
            "validation": 6,
        }
        return priority.get((inference_source or "").lower(), 9)

    @staticmethod
    def _relationship_priority(relationship: InferredRelationship) -> int:
        # Required order:
        # 1) control narrative relationships
        # 2) piping relationships
        # 3) process sequence relationships
        # 4) heuristic proximity relationships
        control_types = {"SIGNAL_TO", "CONTROLS", "INTERLOCKS_WITH", "ALARMS_ON", "MEASURES"}
        piping_types = {"PROCESS_FLOW", "CONNECTED_TO", "SUPPLIES_AIR_TO"}
        sequence_types = {"FEEDS", "DISCHARGES_TO", "PART_OF"}

        if relationship.inference_source == "narrative" or relationship.relationship_type in control_types:
            return 0
        if relationship.relationship_type in piping_types:
            return 1
        if relationship.relationship_type in sequence_types:
            return 2
        if relationship.inference_source in {"heuristic", "locality"}:
            return 3
        return 4

    @staticmethod
    def _is_symmetric_relationship(relationship_type: str) -> bool:
        return relationship_type in {"INTERLOCKS_WITH", "CONNECTED_TO", "ASSOCIATED_WITH"}

    def _entity_bucket(self, entity: EngineeringEntity) -> str:
        ctype = entity.canonical_type
        if ctype == "control_valve":
            return "control_valve"
        if ctype != "process_unit":
            return ctype

        text = f"{entity.id} {entity.display_name}".lower()
        if "air-header" in text or "air header" in text:
            return "air_header"
        if "aeration" in text and "basin" in text:
            return "aeration_basin"
        if "wet-well" in text or "wet well" in text:
            return "wet_well"
        if "tank" in text:
            return "tank"
        if "basin" in text:
            return "basin"
        if "clarifier" in text:
            return "clarifier"
        return "process_unit"

    def _is_structural_edge(self, relationship: InferredRelationship, target: EngineeringEntity) -> bool:
        # Keep topology/cluster anchoring edges outside matrix checks.
        if relationship.relationship_type == "PART_OF":
            return True
        if relationship.relationship_type == "MEASURES" and target.canonical_type == "process_unit":
            return True
        return False

    @staticmethod
    def _target_matches_allowed(target_bucket: str, allowed_bucket: str) -> bool:
        aliases: dict[str, set[str]] = {
            "valve": {"valve", "control_valve"},
            "control_valve": {"control_valve"},
            "basin": {"basin", "aeration_basin"},
            "air_header": {"air_header"},
            "wet_well": {"wet_well"},
            "tank": {"tank"},
            "clarifier": {"clarifier"},
            "pipe": {"pipe"},
            "pump": {"pump"},
        }
        return target_bucket in aliases.get(allowed_bucket, {allowed_bucket})

    def _is_compatible(
        self,
        source: EngineeringEntity,
        target: EngineeringEntity,
        relationship: InferredRelationship,
    ) -> bool:
        source_bucket = self._entity_bucket(source)
        target_bucket = self._entity_bucket(target)

        if source_bucket in self.sensor_types and target_bucket in self.sensor_types:
            return False
        if source_bucket in self.sensor_types and target_bucket == "blower":
            return False
        if source_bucket == "blower" and target_bucket in self.sensor_types:
            return False

        allowed_targets = self.compatibility_matrix.get(source_bucket)
        if allowed_targets is None:
            return False

        for allowed in allowed_targets:
            if self._target_matches_allowed(target_bucket, allowed):
                return True

        return False

    def validate(
        self,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
    ) -> tuple[list[InferredRelationship], list[GraphWarning], list[InferredRelationship]]:
        entity_by_id = {entity.id: entity for entity in entities}
        accepted: list[InferredRelationship] = []
        low_suggestions: list[InferredRelationship] = []
        warnings: list[GraphWarning] = []

        dedup_by_key: dict[tuple[str, str, str], InferredRelationship] = {}
        for relationship in relationships:
            if relationship.confidence_score < 0.5:
                low_suggestions.append(relationship)
                continue

            source = entity_by_id.get(relationship.source_entity)
            target = entity_by_id.get(relationship.target_entity)
            if source is None or target is None:
                warnings.append(
                    GraphWarning(
                        message=f"Dropped relationship {relationship.source_entity}->{relationship.target_entity}: missing node",
                        related_entities=[relationship.source_entity, relationship.target_entity],
                    )
                )
                continue

            if not self._is_structural_edge(relationship, target):
                # Do not allow random cross-cluster connections.
                if source.process_unit and target.process_unit and source.process_unit != target.process_unit:
                    low_suggestions.append(relationship)
                    continue

                # Only allow compatible source->target device categories.
                if not self._is_compatible(source, target, relationship):
                    low_suggestions.append(relationship)
                    continue

            key = (relationship.source_entity, relationship.target_entity, relationship.relationship_type)
            prior = dedup_by_key.get(key)
            if prior is None:
                dedup_by_key[key] = relationship
            else:
                prior_rank = (
                    self._relationship_priority(prior),
                    self._inference_priority(prior.inference_source),
                    -prior.confidence_score,
                )
                new_rank = (
                    self._relationship_priority(relationship),
                    self._inference_priority(relationship.inference_source),
                    -relationship.confidence_score,
                )
                if new_rank < prior_rank:
                    dedup_by_key[key] = relationship

        pruned = list(dedup_by_key.values())

        # Remove symmetric duplicates (A<->B) for symmetric relationship types.
        symmetric_best: dict[tuple[str, str, str], InferredRelationship] = {}
        directional: list[InferredRelationship] = []
        for relationship in pruned:
            if self._is_symmetric_relationship(relationship.relationship_type):
                a, b = sorted([relationship.source_entity, relationship.target_entity])
                sym_key = (a, b, relationship.relationship_type)
                prior = symmetric_best.get(sym_key)
                if prior is None:
                    symmetric_best[sym_key] = relationship
                else:
                    prior_rank = (
                        self._relationship_priority(prior),
                        self._inference_priority(prior.inference_source),
                        -prior.confidence_score,
                    )
                    new_rank = (
                        self._relationship_priority(relationship),
                        self._inference_priority(relationship.inference_source),
                        -relationship.confidence_score,
                    )
                    if new_rank < prior_rank:
                        symmetric_best[sym_key] = relationship
            else:
                directional.append(relationship)

        pruned = [*directional, *symmetric_best.values()]

        # Per-source cap: at most top-N outgoing edges by source priority/confidence.
        by_source: dict[str, list[InferredRelationship]] = defaultdict(list)
        for relationship in pruned:
            by_source[relationship.source_entity].append(relationship)

        for source_id, source_edges in by_source.items():
            # Rule: if source already has valid in-cluster connections, drop cross-cluster options.
            has_in_cluster = False
            for edge in source_edges:
                src = entity_by_id.get(edge.source_entity)
                tgt = entity_by_id.get(edge.target_entity)
                if src is None or tgt is None:
                    continue
                if self._is_structural_edge(edge, tgt):
                    continue
                if src.process_unit and tgt.process_unit and src.process_unit == tgt.process_unit:
                    has_in_cluster = True
                    break

            filtered_source_edges: list[InferredRelationship] = []
            removed_cross_cluster = 0
            for edge in source_edges:
                src = entity_by_id.get(edge.source_entity)
                tgt = entity_by_id.get(edge.target_entity)
                if src is None or tgt is None:
                    continue
                if (
                    has_in_cluster
                    and not self._is_structural_edge(edge, tgt)
                    and src.process_unit
                    and tgt.process_unit
                    and src.process_unit != tgt.process_unit
                ):
                    low_suggestions.append(edge)
                    removed_cross_cluster += 1
                    continue
                filtered_source_edges.append(edge)

            if removed_cross_cluster:
                warnings.append(
                    GraphWarning(
                        message=f"Removed {removed_cross_cluster} cross-cluster edges for {source_id} after finding valid in-cluster process connections.",
                        severity="info",
                        related_entities=[source_id],
                    )
                )

            # Prefer vertical/process-chain edges by tier first, then confidence.
            filtered_source_edges.sort(
                key=lambda edge: (
                    self._relationship_priority(edge),
                    self._inference_priority(edge.inference_source),
                    -edge.confidence_score,
                )
            )
            kept = filtered_source_edges[: self.max_outgoing_edges]
            dropped = filtered_source_edges[self.max_outgoing_edges :]
            accepted.extend(kept)
            low_suggestions.extend(dropped)
            if dropped:
                warnings.append(
                    GraphWarning(
                        message=f"Trimmed {len(dropped)} outgoing edges for {source_id} (max {self.max_outgoing_edges}).",
                        severity="info",
                        related_entities=[source_id],
                    )
                )

        for entity in entities:
            if not entity.is_synthetic and not entity.process_unit:
                warnings.append(
                    GraphWarning(
                        message=f"{entity.id} classified but no reliable process_unit assignment",
                        related_entities=[entity.id],
                    )
                )

        self.logger.info(
            "Graph validation: accepted=%s low_suggestions=%s warnings=%s",
            len(accepted),
            len(low_suggestions),
            len(warnings),
        )
        return accepted, warnings, low_suggestions


graph_validation_service = GraphValidationService()
