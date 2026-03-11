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
    def _confidence(edge_type: str, edge_confidence: float, sensor: str, actuator: str, sensor_unit: str | None, actuator_unit: str | None) -> float:
        score = max(0.35, min(0.98, edge_confidence))
        if edge_type in {"SIGNAL_TO", "CONTROLS"}:
            score += 0.10
        if sensor_unit and actuator_unit and sensor_unit == actuator_unit:
            score += 0.10
        if sensor.startswith(("LT", "LIT", "FT", "PIT", "AIT")) and actuator.startswith(("P", "PMP", "FCV", "VAL", "BL")):
            score += 0.05
        return round(min(score, 0.99), 3)

    def discover(self, project_id: str) -> list[DiscoveredControlLoop]:
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

        loops: list[DiscoveredControlLoop] = []
        for edge in graph.edges:
            edge_type = edge.edge_type.upper()
            source = edge.source.upper()
            target = edge.target.upper()

            if edge_type not in {"SIGNAL_TO", "CONTROLS", "MEASURES", "MONITORS"}:
                continue

            if source in sensors and target in actuators:
                control_strategy = "PID" if node_type_map.get(source) in {"analyzer", "pressure_transmitter"} else "ON_OFF"
                output_tag, command_tag = st_codegen_utils.infer_loop_output_tags(
                    target,
                    node_type_map.get(target),
                    control_strategy,
                )
                confidence = self._confidence(
                    edge_type=edge_type,
                    edge_confidence=edge.confidence,
                    sensor=source,
                    actuator=target,
                    sensor_unit=unit_map.get(source),
                    actuator_unit=unit_map.get(target),
                )
                loops.append(
                    DiscoveredControlLoop(
                        loop_tag=f"LOOP-{source}-{target}",
                        sensor_tag=source,
                        actuator_tag=target,
                        pv_tag=source,
                        sp_tag=f"{source}_SP",
                        output_tag_analog=output_tag if output_tag.endswith("_OUT") else None,
                        command_tag_bool=command_tag,
                        process_unit=unit_map.get(source) or unit_map.get(target),
                        controller_tag=f"LIC-{source.split('-')[-1]}" if source.startswith("L") else None,
                        loop_type="feedback",
                        control_strategy=control_strategy,
                        setpoint_tag=f"{source}_SP",
                        output_tag=output_tag,
                        confidence=confidence,
                        status="inferred",
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
        self._persist(project_id, result)
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
