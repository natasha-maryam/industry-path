from __future__ import annotations

import logging

try:
    import networkx as nx
except Exception:  # pragma: no cover - optional dependency
    nx = None

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

    @staticmethod
    def _humanize_edge_label(edge_type: str) -> str:
        return edge_type.replace("_", " ").title()

    @staticmethod
    def _signal_type(canonical_type: str) -> str | None:
        mapping = {
            "flow_transmitter": "analog",
            "level_transmitter": "analog",
            "pressure_transmitter": "analog",
            "differential_pressure_transmitter": "analog",
            "analyzer": "analog",
            "level_switch": "digital",
            "pump": "digital",
            "valve": "digital",
            "control_valve": "analog",
            "blower": "digital",
        }
        return mapping.get(canonical_type)

    @staticmethod
    def _instrument_role(canonical_type: str) -> str | None:
        mapping = {
            "flow_transmitter": "flow_measurement",
            "level_transmitter": "level_measurement",
            "pressure_transmitter": "pressure_measurement",
            "differential_pressure_transmitter": "pressure_measurement",
            "level_switch": "level_switch",
            "analyzer": "analyzer",
        }
        return mapping.get(canonical_type)

    @staticmethod
    def _control_role(canonical_type: str) -> str:
        if canonical_type in {"pump", "valve", "control_valve", "blower", "chemical_system_device"}:
            return "actuator"
        if canonical_type in {"flow_transmitter", "level_transmitter", "pressure_transmitter", "differential_pressure_transmitter", "level_switch", "analyzer"}:
            return "sensor"
        if canonical_type == "process_unit":
            return "process_unit"
        return "equipment"

    @staticmethod
    def _semantic_kind(relationship_type: str) -> str:
        process = {"PROCESS_FLOW", "CONNECTED_TO", "FEEDS", "DISCHARGES_TO", "SUPPLIES_AIR_TO", "PART_OF"}
        measurement = {"MEASURES", "MONITORS"}
        signal = {"SIGNAL_TO", "CONTROLS", "INTERLOCKS_WITH", "ALARMS_ON", "SUPPORTS"}
        if relationship_type in process:
            return "process_flow"
        if relationship_type in measurement:
            return "measurement_signal"
        if relationship_type in signal:
            return "control_signal"
        return "association"

    @staticmethod
    def _line_style_for_semantic(semantic_kind: str) -> str:
        if semantic_kind == "control_signal":
            return "dashed"
        if semantic_kind == "measurement_signal":
            return "dotted"
        return "solid"

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

    def build(
        self,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
        deep_metadata: dict[str, dict[str, object]] | None = None,
    ) -> tuple[list[dict], list[dict]]:
        entity_by_id = {entity.id: entity for entity in entities}
        metadata_by_id = deep_metadata or {}

        outgoing: dict[str, list[InferredRelationship]] = {}
        incoming: dict[str, list[InferredRelationship]] = {}
        for relationship in relationships:
            outgoing.setdefault(relationship.source_entity, []).append(relationship)
            incoming.setdefault(relationship.target_entity, []).append(relationship)

        control_path_map: dict[str, list[str]] = {}
        if nx is not None:
            control_graph = nx.DiGraph()
            for relationship in relationships:
                if self._semantic_kind(relationship.relationship_type) in {"control_signal", "measurement_signal"}:
                    control_graph.add_edge(relationship.source_entity, relationship.target_entity)
            for entity in entities:
                if entity.id not in control_graph:
                    continue
                predecessors = list(control_graph.predecessors(entity.id))
                if predecessors:
                    control_path_map[entity.id] = [f"{source} → {entity.id}" for source in predecessors[:4]]

        nodes: list[dict] = []
        for entity in entities:
            related_out = outgoing.get(entity.id, [])
            related_in = incoming.get(entity.id, [])
            related = [*related_out, *related_in]
            signal_labels = sorted(
                {
                    item.relationship_type
                    for item in related
                    if self._semantic_kind(item.relationship_type) in {"control_signal", "measurement_signal"}
                }
            )
            controls = sorted(
                {
                    item.target_entity
                    for item in related_out
                    if self._semantic_kind(item.relationship_type) == "control_signal"
                }
            )
            measures = sorted(
                {
                    item.target_entity
                    for item in related_out
                    if self._semantic_kind(item.relationship_type) == "measurement_signal"
                }
            )
            connected_to = sorted(
                {
                    item.target_entity if item.source_entity == entity.id else item.source_entity
                    for item in related
                    if self._semantic_kind(item.relationship_type) in {"process_flow", "association"}
                }
            )

            enriched_metadata = dict(metadata_by_id.get(entity.id, {}))
            enriched_metadata.setdefault("device_type", entity.canonical_type)
            enriched_metadata.setdefault("process_unit", entity.process_unit or "unassigned")
            metadata_confidence = enriched_metadata.get("metadata_confidence", {})
            if not isinstance(metadata_confidence, dict):
                metadata_confidence = {}

            metadata_connected = enriched_metadata.get("connected_to", [])
            if isinstance(metadata_connected, str):
                metadata_connected = [item.strip() for item in metadata_connected.split(",") if item.strip()]
            if not isinstance(metadata_connected, list):
                metadata_connected = []
            merged_connected_to = sorted(set([*connected_to, *[str(item) for item in metadata_connected]]))

            metadata_controls = enriched_metadata.get("controls", [])
            if isinstance(metadata_controls, str):
                metadata_controls = [item.strip() for item in metadata_controls.split(",") if item.strip()]
            if not isinstance(metadata_controls, list):
                metadata_controls = []
            merged_controls = sorted(set([*controls, *[str(item) for item in metadata_controls]]))

            metadata_measures = enriched_metadata.get("measures", [])
            if isinstance(metadata_measures, str):
                metadata_measures = [item.strip() for item in metadata_measures.split(",") if item.strip()]
            if not isinstance(metadata_measures, list):
                metadata_measures = []
            merged_measures = sorted(set([*measures, *[str(item) for item in metadata_measures]]))

            metadata_control_path = enriched_metadata.get("control_path", [])
            if isinstance(metadata_control_path, str):
                metadata_control_path = [metadata_control_path]
            if not isinstance(metadata_control_path, list):
                metadata_control_path = []
            merged_control_path = [str(item) for item in metadata_control_path] or control_path_map.get(entity.id, [])

            nodes.append(
                GraphNode(
                    id=entity.id,
                    label=entity.display_name,
                    node_type=entity.canonical_type,
                    status="parsed",
                    description="; ".join(entity.parse_notes) if entity.parse_notes else None,
                    source_documents=entity.source_documents,
                    signals=signal_labels,
                    alarms=[item.source_entity for item in related_in if item.relationship_type == "ALARMS_ON"],
                    interlocks=[item.source_entity for item in related_in if item.relationship_type == "INTERLOCKS_WITH"],
                    mode=entity.process_unit,
                    linked_logic=[item.relationship_type for item in related if self._semantic_kind(item.relationship_type) == "control_logic"],
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
                    equipment_type=str(enriched_metadata.get("equipment_type") or entity.canonical_type),
                    signal_type=(
                        str(enriched_metadata.get("signal_type"))
                        if enriched_metadata.get("signal_type") is not None
                        else self._signal_type(entity.canonical_type)
                    ),
                    instrument_role=(
                        str(enriched_metadata.get("instrument_role"))
                        if enriched_metadata.get("instrument_role") is not None
                        else self._instrument_role(entity.canonical_type)
                    ),
                    control_role=(
                        str(enriched_metadata.get("control_role"))
                        if enriched_metadata.get("control_role") is not None
                        else self._control_role(entity.canonical_type)
                    ),
                    power_rating=enriched_metadata.get("power_rating"),
                    connected_to=merged_connected_to,
                    controls=merged_controls,
                    measures=merged_measures,
                    control_path=merged_control_path,
                    metadata=enriched_metadata,
                    metadata_confidence={str(key): float(value) for key, value in metadata_confidence.items() if isinstance(value, (int, float))},
                ).model_dump()
            )

        edges: list[dict] = []
        edge_keys: set[tuple[str, str, str]] = set()
        for relationship in relationships:
            edge_class, fallback_line_style = self._classify_edge(relationship, entity_by_id)
            semantic_kind = self._semantic_kind(relationship.relationship_type)
            line_style = self._line_style_for_semantic(semantic_kind) if semantic_kind != "association" else fallback_line_style
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
                    edge_label=self._humanize_edge_label(relationship.relationship_type),
                    semantic_kind=semantic_kind,
                    process_flow_direction="forward" if semantic_kind == "process_flow" else None,
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
                        edge_label="Signal",
                        semantic_kind="signal",
                    ).model_dump()
                )

        self.logger.info("Graph build output: nodes=%s edges=%s", len(nodes), len(edges))
        return nodes, edges


graph_build_service = GraphBuildService()
