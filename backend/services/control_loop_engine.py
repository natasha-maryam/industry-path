from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any
from uuid import uuid4

from db.neo4j import neo4j_client
from models.control_loop import ControlLoopRecord
from models.logic import DiscoveredControlLoop
from services.control_loop_store import control_loop_store
from services.graph_service import graph_service


class ControlLoopEngine:
    SENSOR_NODE_TYPES = {
        "sensor",
        "switch",
        "analyzer",
        "flow_transmitter",
        "level_transmitter",
        "pressure_transmitter",
        "differential_pressure_transmitter",
        "temperature_transmitter",
        "level_switch",
    }
    PROCESS_NODE_TYPES = {
        "process",
        "process_unit",
        "tank",
        "basin",
        "clarifier",
        "reactor",
    }
    ACTUATOR_NODE_TYPES = {
        "actuator",
        "pump",
        "valve",
        "control_valve",
        "blower",
        "motor",
        "chemical_system_device",
    }

    MEASURE_RELATION_NAMES = {
        "MEASURES",
        "MONITORS",
        "SIGNAL_TO",
    }
    CONTROL_RELATION_NAMES = {
        "CONTROLS",
        "SIGNAL_TO",
    }
    GENERIC_RELATION_NAMES = {
        "CONNECTED_TO",
        "AFFECTS",
        "PART_OF",
        "FEEDS",
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _normalize_token(value: str) -> str:
        token = re.sub(r"[^A-Za-z0-9]+", "_", (value or "").upper()).strip("_")
        return token or "UNKNOWN"

    def _make_loop_tag(self, sensor_tag: str, actuator_tag: str) -> str:
        return f"LOOP_{self._normalize_token(sensor_tag)}_{self._normalize_token(actuator_tag)}"

    @staticmethod
    def _infer_controller_tag(sensor_tag: str, process_unit: str) -> str:
        base = process_unit or sensor_tag
        return f"CTRL_{re.sub(r'[^A-Za-z0-9]+', '_', base).strip('_').upper()}"

    @staticmethod
    def _safe_upper(value: Any) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def _safe_lower(value: Any) -> str:
        return str(value or "").strip().lower()

    def _is_sensor_node(self, row: dict[str, Any]) -> bool:
        labels = {self._safe_upper(label) for label in row.get("labels", [])}
        node_type = self._safe_lower(row.get("node_type"))
        equipment_type = self._safe_lower(row.get("equipment_type"))
        control_role = self._safe_lower(row.get("control_role"))
        instrument_role = self._safe_lower(row.get("instrument_role"))

        if "SENSOR" in labels:
            return True
        if node_type in self.SENSOR_NODE_TYPES or equipment_type in self.SENSOR_NODE_TYPES:
            return True
        if control_role == "sensor":
            return True
        return any(token in instrument_role for token in {"measurement", "analyzer", "switch"})

    def _is_process_node(self, row: dict[str, Any]) -> bool:
        labels = {self._safe_upper(label) for label in row.get("labels", [])}
        node_type = self._safe_lower(row.get("node_type"))
        equipment_type = self._safe_lower(row.get("equipment_type"))
        control_role = self._safe_lower(row.get("control_role"))

        if "PROCESS" in labels:
            return True
        if node_type in self.PROCESS_NODE_TYPES or equipment_type in self.PROCESS_NODE_TYPES:
            return True
        return control_role in {"process", "process_unit"}

    def _is_actuator_node(self, row: dict[str, Any]) -> bool:
        labels = {self._safe_upper(label) for label in row.get("labels", [])}
        node_type = self._safe_lower(row.get("node_type"))
        equipment_type = self._safe_lower(row.get("equipment_type"))
        control_role = self._safe_lower(row.get("control_role"))

        if "ACTUATOR" in labels:
            return True
        if node_type in self.ACTUATOR_NODE_TYPES or equipment_type in self.ACTUATOR_NODE_TYPES:
            return True
        return control_role == "actuator"

    def _normalize_relationship(
        self,
        raw_edge_type: str,
        relation_type: str,
        semantic_kind: str,
        source_is_sensor: bool,
        source_is_process: bool,
        source_is_actuator: bool,
        target_is_sensor: bool,
        target_is_process: bool,
        target_is_actuator: bool,
    ) -> str | None:
        edge_name = self._safe_upper(raw_edge_type) or self._safe_upper(relation_type)
        semantic = self._safe_upper(semantic_kind)

        if semantic == "MEASUREMENT_SIGNAL":
            return "MEASURES"
        if semantic == "CONTROL_SIGNAL":
            return "CONTROLS"

        if edge_name in self.MEASURE_RELATION_NAMES:
            return "MEASURES"
        if edge_name in self.CONTROL_RELATION_NAMES:
            return "CONTROLS"

        if edge_name in self.GENERIC_RELATION_NAMES:
            if (source_is_sensor and target_is_process) or (target_is_sensor and source_is_process):
                return "MEASURES"
            if (source_is_actuator and target_is_process) or (target_is_actuator and source_is_process):
                return "CONTROLS"

        return None

    def _fetch_node_rows(self, project_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (n {project_id: $project_id})
        RETURN n.id AS id,
               labels(n) AS labels,
               coalesce(n.node_type, '') AS node_type,
               coalesce(n.equipment_type, '') AS equipment_type,
               coalesce(n.control_role, '') AS control_role,
               coalesce(n.instrument_role, '') AS instrument_role,
               coalesce(n.process_unit, n.id) AS process_unit,
               coalesce(n.signal_type, '') AS signal_type
        """
        with neo4j_client.driver.session() as session:
            return [dict(row) for row in session.run(query, project_id=project_id)]

    def _fetch_edge_rows(self, project_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (a {project_id: $project_id})-[r]-(b {project_id: $project_id})
        RETURN a.id AS source_tag,
               labels(a) AS source_labels,
               coalesce(a.node_type, '') AS source_node_type,
               coalesce(a.equipment_type, '') AS source_equipment_type,
               coalesce(a.control_role, '') AS source_control_role,
               coalesce(a.instrument_role, '') AS source_instrument_role,
               coalesce(a.process_unit, a.id) AS source_process_unit,
               b.id AS target_tag,
               labels(b) AS target_labels,
               coalesce(b.node_type, '') AS target_node_type,
               coalesce(b.equipment_type, '') AS target_equipment_type,
               coalesce(b.control_role, '') AS target_control_role,
               coalesce(b.instrument_role, '') AS target_instrument_role,
               coalesce(b.process_unit, b.id) AS target_process_unit,
               toUpper(coalesce(properties(r)['edge_type'], type(r), '')) AS raw_edge_type,
               toUpper(type(r)) AS relation_type,
               toUpper(coalesce(properties(r)['semantic_kind'], '')) AS semantic_kind,
               coalesce(r.confidence, 0.70) AS confidence
        """
        with neo4j_client.driver.session() as session:
            return [dict(row) for row in session.run(query, project_id=project_id)]

    def _fallback_rows_from_graph_cache(self, project_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        graph = graph_service.get_graph(project_id)
        node_by_id = {node.id: node for node in graph.nodes}

        node_rows: list[dict[str, Any]] = [
            {
                "id": node.id,
                "labels": ["Device"],
                "node_type": node.node_type,
                "equipment_type": node.equipment_type,
                "control_role": node.control_role,
                "instrument_role": node.instrument_role,
                "process_unit": node.process_unit or node.id,
                "signal_type": node.signal_type,
            }
            for node in graph.nodes
        ]

        edge_rows: list[dict[str, Any]] = []
        for edge in graph.edges:
            source = node_by_id.get(edge.source)
            target = node_by_id.get(edge.target)
            if source is None or target is None:
                continue
            edge_rows.append(
                {
                    "source_tag": source.id,
                    "source_labels": ["Device"],
                    "source_node_type": source.node_type,
                    "source_equipment_type": source.equipment_type,
                    "source_control_role": source.control_role,
                    "source_instrument_role": source.instrument_role,
                    "source_process_unit": source.process_unit or source.id,
                    "target_tag": target.id,
                    "target_labels": ["Device"],
                    "target_node_type": target.node_type,
                    "target_equipment_type": target.equipment_type,
                    "target_control_role": target.control_role,
                    "target_instrument_role": target.instrument_role,
                    "target_process_unit": target.process_unit or target.id,
                    "raw_edge_type": self._safe_upper(edge.edge_type),
                    "relation_type": self._safe_upper(edge.edge_type),
                    "semantic_kind": self._safe_upper(edge.semantic_kind),
                    "confidence": float(edge.confidence or 0.70),
                }
            )

        return node_rows, edge_rows

    def _collect_detection_rows(
        self, project_id: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
        node_rows = self._fetch_node_rows(project_id)
        edge_rows = self._fetch_edge_rows(project_id)
        data_source = "neo4j"

        if not node_rows and not edge_rows:
            node_rows, edge_rows = self._fallback_rows_from_graph_cache(project_id)
            data_source = "workspace_graph_cache"

        sensor_nodes = 0
        process_nodes = 0
        actuator_nodes = 0
        for node in node_rows:
            if self._is_sensor_node(node):
                sensor_nodes += 1
            if self._is_process_node(node):
                process_nodes += 1
            if self._is_actuator_node(node):
                actuator_nodes += 1

        sensor_rows: list[dict[str, Any]] = []
        actuator_rows: list[dict[str, Any]] = []
        exact_measures_edges = 0
        exact_controls_edges = 0

        for edge in edge_rows:
            source_node = {
                "labels": edge.get("source_labels", []),
                "node_type": edge.get("source_node_type"),
                "equipment_type": edge.get("source_equipment_type"),
                "control_role": edge.get("source_control_role"),
                "instrument_role": edge.get("source_instrument_role"),
            }
            target_node = {
                "labels": edge.get("target_labels", []),
                "node_type": edge.get("target_node_type"),
                "equipment_type": edge.get("target_equipment_type"),
                "control_role": edge.get("target_control_role"),
                "instrument_role": edge.get("target_instrument_role"),
            }

            source_is_sensor = self._is_sensor_node(source_node)
            source_is_process = self._is_process_node(source_node)
            source_is_actuator = self._is_actuator_node(source_node)
            target_is_sensor = self._is_sensor_node(target_node)
            target_is_process = self._is_process_node(target_node)
            target_is_actuator = self._is_actuator_node(target_node)

            raw_edge_type = self._safe_upper(edge.get("raw_edge_type"))
            relation_type = self._safe_upper(edge.get("relation_type"))
            semantic_kind = self._safe_upper(edge.get("semantic_kind"))

            if raw_edge_type == "MEASURES" or relation_type == "MEASURES":
                exact_measures_edges += 1
            if raw_edge_type == "CONTROLS" or relation_type == "CONTROLS":
                exact_controls_edges += 1

            normalized = self._normalize_relationship(
                raw_edge_type=raw_edge_type,
                relation_type=relation_type,
                semantic_kind=semantic_kind,
                source_is_sensor=source_is_sensor,
                source_is_process=source_is_process,
                source_is_actuator=source_is_actuator,
                target_is_sensor=target_is_sensor,
                target_is_process=target_is_process,
                target_is_actuator=target_is_actuator,
            )
            if normalized is None:
                continue

            if normalized == "MEASURES":
                if source_is_sensor and target_is_process:
                    sensor_rows.append(
                        {
                            "sensor_tag": str(edge.get("source_tag") or ""),
                            "process_unit": str(edge.get("target_process_unit") or edge.get("target_tag") or "UNKNOWN"),
                            "confidence": float(edge.get("confidence") or 0.70),
                            "raw_edge_type": raw_edge_type or relation_type,
                            "normalized_edge_type": "MEASURES",
                        }
                    )
                elif target_is_sensor and source_is_process:
                    sensor_rows.append(
                        {
                            "sensor_tag": str(edge.get("target_tag") or ""),
                            "process_unit": str(edge.get("source_process_unit") or edge.get("source_tag") or "UNKNOWN"),
                            "confidence": float(edge.get("confidence") or 0.70),
                            "raw_edge_type": raw_edge_type or relation_type,
                            "normalized_edge_type": "MEASURES",
                        }
                    )

            if normalized == "CONTROLS":
                if source_is_actuator and target_is_process:
                    actuator_rows.append(
                        {
                            "actuator_tag": str(edge.get("source_tag") or ""),
                            "process_unit": str(edge.get("target_process_unit") or edge.get("target_tag") or "UNKNOWN"),
                            "confidence": float(edge.get("confidence") or 0.70),
                            "raw_edge_type": raw_edge_type or relation_type,
                            "normalized_edge_type": "CONTROLS",
                        }
                    )
                elif target_is_actuator and source_is_process:
                    actuator_rows.append(
                        {
                            "actuator_tag": str(edge.get("target_tag") or ""),
                            "process_unit": str(edge.get("source_process_unit") or edge.get("source_tag") or "UNKNOWN"),
                            "confidence": float(edge.get("confidence") or 0.70),
                            "raw_edge_type": raw_edge_type or relation_type,
                            "normalized_edge_type": "CONTROLS",
                        }
                    )

        stats = {
            "data_source": data_source,
            "total_sensor_nodes": sensor_nodes,
            "total_process_nodes": process_nodes,
            "total_actuator_nodes": actuator_nodes,
            "total_measures_edges": exact_measures_edges,
            "total_controls_edges": exact_controls_edges,
            "normalized_measures_rows": len(sensor_rows),
            "normalized_controls_rows": len(actuator_rows),
        }
        return sensor_rows, actuator_rows, stats

    def debug_snapshot(self, project_id: str) -> dict[str, Any]:
        sensor_rows, actuator_rows, stats = self._collect_detection_rows(project_id)
        return {
            "project_id": project_id,
            **stats,
            "sensor_process_rows": sensor_rows,
            "actuator_process_rows": actuator_rows,
        }

    def detect(self, project_id: str) -> list[ControlLoopRecord]:
        debug = self.debug_snapshot(project_id)
        self.logger.info(
            "Control loop detect graph snapshot: project=%s sensors=%s processes=%s actuators=%s measures=%s controls=%s",
            project_id,
            debug["total_sensor_nodes"],
            debug["total_process_nodes"],
            debug["total_actuator_nodes"],
            debug["total_measures_edges"],
            debug["total_controls_edges"],
        )
        self.logger.info(
            "Control loop detect query rows: project=%s sensor_process_rows=%s actuator_process_rows=%s",
            project_id,
            debug["sensor_process_rows"],
            debug["actuator_process_rows"],
        )

        sensor_pairs = debug["sensor_process_rows"]
        actuator_pairs = debug["actuator_process_rows"]

        sensors_by_process: dict[str, list[dict[str, Any]]] = defaultdict(list)
        actuators_by_process: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in sensor_pairs:
            process_key = str(row.get("process_unit") or "UNKNOWN")
            sensors_by_process[process_key].append(row)
        for row in actuator_pairs:
            process_key = str(row.get("process_unit") or "UNKNOWN")
            actuators_by_process[process_key].append(row)

        inferred: list[ControlLoopRecord] = []
        for process_unit in sorted(set([*sensors_by_process.keys(), *actuators_by_process.keys()])):
            sensors = sensors_by_process.get(process_unit, [])
            actuators = actuators_by_process.get(process_unit, [])
            if not sensors or not actuators:
                continue

            for sensor in sensors:
                for actuator in actuators:
                    sensor_tag = str(sensor.get("sensor_tag") or "")
                    actuator_tag = str(actuator.get("actuator_tag") or "")
                    if not sensor_tag or not actuator_tag:
                        continue
                    score = round(
                        max(
                            0.0,
                            min(
                                1.0,
                                (
                                    (float(sensor.get("confidence") or 0.7) + float(actuator.get("confidence") or 0.7)) / 2.0
                                ),
                            ),
                        ),
                        3,
                    )
                    inferred.append(
                        ControlLoopRecord(
                            id=str(uuid4()),
                            project_id=project_id,
                            loop_tag=self._make_loop_tag(sensor_tag, actuator_tag),
                            sensor_tag=sensor_tag,
                            actuator_tag=actuator_tag,
                            process_unit=process_unit,
                            controller_tag=self._infer_controller_tag(sensor_tag, process_unit),
                            loop_type="feedback",
                            control_strategy="PID",
                            setpoint_tag=f"{sensor_tag}_SP",
                            output_tag=f"{actuator_tag}_OUT",
                            status="inferred",
                            confidence=score,
                        )
                    )

        dedup: dict[tuple[str, str, str], ControlLoopRecord] = {}
        for loop in inferred:
            key = (loop.process_unit or "", loop.sensor_tag, loop.actuator_tag)
            current = dedup.get(key)
            if current is None or loop.confidence > current.confidence:
                dedup[key] = loop

        detected = sorted(dedup.values(), key=lambda item: (item.process_unit or "", item.sensor_tag, item.actuator_tag))
        self.logger.info("Control loop detect completed: project=%s detected=%s", project_id, len(detected))
        return detected

    def detect_and_store(self, project_id: str) -> list[ControlLoopRecord]:
        loops = self.detect(project_id)
        stored = control_loop_store.upsert_project_loops(project_id, loops)
        if not stored:
            self.logger.info("Control loop discovery found no loops: project=%s", project_id)
        else:
            self.logger.info("Control loop discovery completed: project=%s loops=%s", project_id, len(stored))
        return stored

    def discover(self, project_id: str, *, persist: bool = True) -> list[DiscoveredControlLoop]:
        loops = self.detect_and_store(project_id) if persist else self.detect(project_id)
        return [
            DiscoveredControlLoop(
                loop_tag=item.loop_tag,
                sensor_tag=item.sensor_tag,
                actuator_tag=item.actuator_tag,
                process_unit=item.process_unit,
                controller_tag=item.controller_tag,
                loop_type=item.loop_type,
                control_strategy=item.control_strategy,
                setpoint_tag=item.setpoint_tag,
                output_tag=item.output_tag,
                confidence=item.confidence,
                status="inferred",
                source_reference="neo4j: normalized sensor/process/actuator relationship mapping",
            )
            for item in loops
        ]


control_loop_engine = ControlLoopEngine()
