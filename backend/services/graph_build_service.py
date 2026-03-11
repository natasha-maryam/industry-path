from __future__ import annotations

import logging

from models.graph import GraphEdge, GraphNode
from models.pipeline import EngineeringEntity, InferredRelationship


class GraphBuildService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.sensor_types = {
            "analyzer",
            "flow_transmitter",
            "level_transmitter",
            "pressure_transmitter",
            "differential_pressure_transmitter",
            "level_switch",
        }
        self.process_edge_types = {
            "PROCESS_FLOW",
            "CONNECTED_TO",
            "FEEDS",
            "DISCHARGES_TO",
            "SUPPLIES_AIR_TO",
            "PART_OF",
        }
        self.monitoring_edge_types = {
            "MEASURES",
            "MONITORS",
            "SIGNAL_TO",
        }
        self.process_edge_creators = {
            "pump",
            "valve",
            "control_valve",
            "blower",
            "pipe",
            "process_unit",
        }

    def _classify_edge(self, relationship: InferredRelationship, entity_by_id: dict[str, EngineeringEntity]) -> tuple[str, str]:
        source = entity_by_id.get(relationship.source_entity)
        target = entity_by_id.get(relationship.target_entity)
        source_type = source.canonical_type if source else "unknown"
        target_type = target.canonical_type if target else "unknown"

        # Sensors are monitoring-only and must not appear in process chain.
        if source_type in self.sensor_types:
            return "monitoring", "dashed"

        # Sensor->process-unit observation edges remain monitoring.
        if target_type == "process_unit" and relationship.relationship_type in self.monitoring_edge_types:
            return "monitoring", "dashed"

        if relationship.relationship_type in self.monitoring_edge_types:
            return "monitoring", "dashed"

        if source_type in self.process_edge_creators and relationship.relationship_type in self.process_edge_types:
            return "process", "solid"

        # Fallback for non-sensor edges keeps physical topology readable.
        return "process", "solid"

    def build(self, entities: list[EngineeringEntity], relationships: list[InferredRelationship]) -> tuple[list[dict], list[dict]]:
        entity_by_id = {entity.id: entity for entity in entities}
        nodes = [
            GraphNode(
                id=entity.id,
                label=entity.display_name,
                node_type=entity.canonical_type,
                status="parsed",
                description="; ".join(entity.parse_notes) if entity.parse_notes else None,
                source_documents=entity.source_documents,
                signals=[],
                alarms=[],
                interlocks=[],
                mode=entity.process_unit,
                linked_logic=[],
                process_unit=entity.process_unit,
                cluster_id=entity.cluster_id,
                cluster_name=entity.cluster_name,
                cluster_order=entity.cluster_order,
                node_rank=entity.node_rank,
                preferred_direction=entity.preferred_direction,
                confidence=entity.confidence,
                is_synthetic=entity.is_synthetic,
                explanation=entity.explanation,
                source_references=entity.source_references,
            ).model_dump()
            for entity in entities
        ]

        edges: list[dict] = []
        edge_keys: set[tuple[str, str, str]] = set()
        for relationship in relationships:
            edge_class, line_style = self._classify_edge(relationship, entity_by_id)
            key = (relationship.source_entity, relationship.target_entity, relationship.relationship_type)
            if key in edge_keys:
                continue
            edge_keys.add(key)
            edges.append(
                GraphEdge(
                    id=f"{relationship.source_entity}__{relationship.relationship_type}__{relationship.target_entity}",
                    source=relationship.source_entity,
                    target=relationship.target_entity,
                    edge_type=relationship.relationship_type,
                    edge_class=edge_class,
                    line_style=line_style,
                    confidence=relationship.confidence_score,
                    explanation=relationship.explanation,
                    inference_source=relationship.inference_source,
                    source_references=relationship.source_references,
                ).model_dump()
            )

        # Deterministic augmentation: connect sensors to actuators in same process unit when no explicit signal edge exists.
        sensors = [item for item in entities if item.canonical_type in self.sensor_types and item.process_unit]
        actuators = [item for item in entities if item.canonical_type in {"pump", "valve", "control_valve", "blower", "chemical_system_device"} and item.process_unit]
        for sensor in sensors:
            for actuator in actuators:
                if sensor.process_unit != actuator.process_unit:
                    continue
                key = (sensor.id, actuator.id, "SIGNAL_TO")
                if key in edge_keys:
                    continue
                edge_keys.add(key)
                edges.append(
                    GraphEdge(
                        id=f"{sensor.id}__SIGNAL_TO__{actuator.id}",
                        source=sensor.id,
                        target=actuator.id,
                        edge_type="SIGNAL_TO",
                        edge_class="monitoring",
                        line_style="dashed",
                        confidence=0.62,
                        explanation="Deterministic process-unit signal edge synthesis.",
                        inference_source="validation",
                        source_references=["graph_build_service:unit_signal_synthesis"],
                    ).model_dump()
                )

        self.logger.info("Graph build output: nodes=%s edges=%s", len(nodes), len(edges))
        return nodes, edges


graph_build_service = GraphBuildService()
