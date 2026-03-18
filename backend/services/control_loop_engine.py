from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from psycopg2.extras import Json

from db.neo4j import neo4j_client
from db.postgres import postgres_client
from models.logic import DiscoveredControlLoop
from models.graph import GraphEdge, GraphNode
from models.graph import PlantGraph
from services.graph_service import graph_service
from services.signal_classification import controller_type_from_sensor, normalize_tag, process_role_from_node
from services.st_codegen_utils import st_codegen_utils


class ControlLoopEngine:
    """Discover control loops from graph relationships and persist best-effort snapshots."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def _load_graph(self, project_id: str) -> PlantGraph:
        try:
            nodes, edges = neo4j_client.fetch_project_graph(project_id)
            if nodes or edges:
                return PlantGraph(
                    project_id=project_id,
                    nodes=[GraphNode.model_validate(node) for node in nodes],
                    edges=[GraphEdge.model_validate(edge) for edge in edges],
                )
        except Exception:
            # Neo4j may be offline in local mode; use cached graph JSON.
            pass
        return graph_service.get_graph(project_id)

    @staticmethod
    def _node_type_map(graph: PlantGraph) -> dict[str, str]:
        return {node.id.upper(): node.node_type for node in graph.nodes}

    @staticmethod
    def _node_unit_map(graph: PlantGraph) -> dict[str, str | None]:
        return {node.id.upper(): node.process_unit for node in graph.nodes}

    @staticmethod
    def _confidence(
        measure_confidence: float,
        control_confidence: float,
        signal_confidence: float | None,
        same_unit: bool,
    ) -> float:
        base = (0.42 * max(0.35, min(0.99, measure_confidence))) + (0.42 * max(0.35, min(0.99, control_confidence)))
        if signal_confidence is not None:
            base += 0.12 * max(0.35, min(0.99, signal_confidence))
        else:
            base += 0.06
        if same_unit:
            base += 0.06
        return round(min(base, 0.99), 3)

    @staticmethod
    def _loop_tag(sensor: str, process: str, actuator: str) -> str:
        sensor_token = normalize_tag(sensor)
        actuator_token = normalize_tag(actuator)
        return f"LOOP_{sensor_token}_{actuator_token}"

    def discover(self, project_id: str, *, persist: bool = True) -> list[DiscoveredControlLoop]:
        graph = self._load_graph(project_id)
        node_type_map = self._node_type_map(graph)
        unit_map = self._node_unit_map(graph)

        sensors = {
            node_id
            for node_id, node_type in node_type_map.items()
            if node_type
            in {
                "flow_transmitter",
                "level_transmitter",
                "level_switch",
                "pressure_transmitter",
                "differential_pressure_transmitter",
                "analyzer",
            }
        }
        actuators = {
            node_id
            for node_id, node_type in node_type_map.items()
            if node_type in {"pump", "control_valve", "valve", "blower", "chemical_system_device"}
        }

        process_nodes = {
            node_id
            for node_id, node_type in node_type_map.items()
            if process_role_from_node(node_type) == "process"
        }

        measures_by_process: dict[str, list[tuple[str, float]]] = {}
        controls_by_process: dict[str, list[tuple[str, float]]] = {}
        direct_signal: dict[tuple[str, str], float] = {}

        for edge in graph.edges:
            edge_type = edge.edge_type.upper()
            source = edge.source.upper()
            target = edge.target.upper()
            if edge_type in {"MEASURES", "MONITORS"} and source in sensors and target in process_nodes:
                measures_by_process.setdefault(target, []).append((source, edge.confidence))
            if edge_type in {"MEASURES", "MONITORS"} and target in sensors and source in process_nodes:
                measures_by_process.setdefault(source, []).append((target, edge.confidence))
            if edge_type == "CONTROLS" and source in actuators and target in process_nodes:
                controls_by_process.setdefault(target, []).append((source, edge.confidence))
            if edge_type == "CONTROLS" and target in actuators and source in process_nodes:
                controls_by_process.setdefault(source, []).append((target, edge.confidence))
            if edge_type in {"SIGNAL_TO", "CONTROLS"} and source in sensors and target in actuators:
                direct_signal[(source, target)] = max(direct_signal.get((source, target), 0.0), edge.confidence)

        # Legacy-graph fallback: infer sensor/actuator process membership from node.process_unit when
        # explicit MEASURES/CONTROLS-to-process edges are missing.
        for node_id, unit in unit_map.items():
            if not unit:
                continue
            process_id = unit.upper()
            if process_id not in process_nodes:
                continue
            node_type = node_type_map.get(node_id)
            role = process_role_from_node(node_type)
            if role == "sensor":
                measures_by_process.setdefault(process_id, []).append((node_id, 0.6))
            elif role == "actuator":
                controls_by_process.setdefault(process_id, []).append((node_id, 0.6))

        loops: list[DiscoveredControlLoop] = []
        for process_id in sorted(set([*measures_by_process.keys(), *controls_by_process.keys()])):
            measure_items = measures_by_process.get(process_id, [])
            control_items = controls_by_process.get(process_id, [])
            if not measure_items or not control_items:
                continue

            for sensor, measure_conf in measure_items:
                for actuator, control_conf in control_items:
                    signal_conf = direct_signal.get((sensor, actuator))
                    strategy = controller_type_from_sensor(sensor, node_type_map.get(sensor))
                    output_tag, command_tag = st_codegen_utils.infer_loop_output_tags(actuator, node_type_map.get(actuator), strategy)
                    confidence = self._confidence(
                        measure_confidence=measure_conf,
                        control_confidence=control_conf,
                        signal_confidence=signal_conf,
                        same_unit=(unit_map.get(sensor) and unit_map.get(sensor) == unit_map.get(actuator)),
                    )
                    loops.append(
                        DiscoveredControlLoop(
                            loop_tag=self._loop_tag(sensor, process_id, actuator),
                            sensor_tag=sensor,
                            actuator_tag=actuator,
                            pv_tag=sensor,
                            sp_tag=f"{sensor}_SP",
                            output_tag_analog=output_tag if output_tag.endswith("_OUT") else None,
                            command_tag_bool=command_tag,
                            process_unit=process_id,
                            controller_tag=f"CTRL-{sensor.split('-')[-1]}" if "-" in sensor else None,
                            loop_type="feedback",
                            control_strategy=strategy,
                            setpoint_tag=f"{sensor}_SP",
                            output_tag=output_tag,
                            confidence=confidence,
                            status="inferred",
                            source_reference="sensor_measures_process + actuator_controls_process",
                        )
                    )

        # Deterministic dedup by (sensor, actuator)
        dedup: dict[tuple[str, str], DiscoveredControlLoop] = {}
        for loop in loops:
            key = (loop.sensor_tag, loop.actuator_tag)
            current = dedup.get(key)
            if current is None or loop.confidence > current.confidence:
                dedup[key] = loop

        result = sorted(dedup.values(), key=lambda item: (item.process_unit or "", item.sensor_tag, item.actuator_tag))
        if persist:
            try:
                self._persist(project_id, result)
            except Exception as exc:
                self.logger.warning("Control loop persistence skipped due to error: %s", exc)
        self.logger.info("Control loop discovery completed: project=%s loops=%s", project_id, len(result))
        return result

    def _latest_parse_batch_id(self, project_id: str) -> str | None:
        row = postgres_client.fetch_one(
            """
            SELECT id::text AS id
            FROM parse_batches
            WHERE project_id = %s
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (project_id,),
        )
        return str(row.get("id")) if row else None

    def _persist(self, project_id: str, loops: list[DiscoveredControlLoop]) -> None:
        if not loops:
            return

        parse_batch_id = self._latest_parse_batch_id(project_id)
        if not parse_batch_id:
            # TODO: Add dedicated control loop store keyed by logic_run_id when parse batch is unavailable.
            return

        now = datetime.now(timezone.utc)
        postgres_client.execute(
            """
            DELETE FROM control_loop_definitions
            WHERE project_id = %s
                AND parse_batch_id = %s
                AND source_sentence LIKE 'Inferred loop:%%'
            """,
            (project_id, parse_batch_id),
        )
        for loop in loops:
            postgres_client.execute(
                """
                INSERT INTO control_loop_definitions (
                    id, project_id, parse_batch_id, name, source_sentence, page_number, related_tags, confidence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    loop.loop_tag,
                    f"Inferred loop: {loop.sensor_tag} -> {loop.actuator_tag}",
                    0,
                    Json([loop.sensor_tag, loop.actuator_tag, loop.process_unit]),
                    loop.confidence,
                    now,
                ),
            )


control_loop_engine = ControlLoopEngine()
