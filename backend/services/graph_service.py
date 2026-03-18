import json
import re
from collections import defaultdict, deque

from db.neo4j import neo4j_client
from models.graph import GraphEdge, GraphNode, PlantGraph, PlantSignalRow, TraceResponse
from services.project_service import project_service
from services.signal_classification import classification_confidence, normalize_tag, process_role_from_node, signal_type_from_tag


class GraphService:
    @staticmethod
    def _loop_id(sensor_tag: str, actuator_tag: str) -> str:
        left = re.sub(r"[^A-Z0-9]+", "_", sensor_tag.upper()).strip("_")
        right = re.sub(r"[^A-Z0-9]+", "_", actuator_tag.upper()).strip("_")
        return f"LOOP_{left}_{right}"

    def _graph_file(self, project_id: str):
        paths = project_service.workspace_paths(project_id)
        return paths.plant_graph / "latest_graph.json"

    def store_graph(self, project_id: str, nodes: list[dict], edges: list[dict]) -> PlantGraph:
        project_service.ensure_project(project_id)

        node_models = [GraphNode.model_validate(node) for node in nodes]
        edge_models = [GraphEdge.model_validate(edge) for edge in edges]

        graph_file = self._graph_file(project_id)
        payload = {
            "project_id": project_id,
            "nodes": [node.model_dump() for node in node_models],
            "edges": [edge.model_dump() for edge in edge_models],
        }
        graph_file.write_text(json.dumps(payload, indent=2))

        try:
            neo4j_client.clear_project_graph(project_id)
            neo4j_client.write_project_graph(
                project_id,
                nodes=[node.model_dump() for node in node_models],
                edges=[edge.model_dump() for edge in edge_models],
            )
        except Exception:
            # Fallback cache remains available when Neo4j is offline.
            pass

        return PlantGraph(project_id=project_id, nodes=node_models, edges=edge_models)

    def _load_graph(self, project_id: str) -> PlantGraph:
        try:
            nodes, edges = neo4j_client.fetch_project_graph(project_id)
            if nodes or edges:
                node_models = [GraphNode.model_validate(node) for node in nodes]
                edge_models = [GraphEdge.model_validate(edge) for edge in edges]
                return PlantGraph(project_id=project_id, nodes=node_models, edges=edge_models)
        except Exception:
            pass

        graph_file = self._graph_file(project_id)
        if not graph_file.exists():
            return PlantGraph(project_id=project_id, nodes=[], edges=[])

        payload = json.loads(graph_file.read_text())
        nodes = [GraphNode.model_validate(node) for node in payload.get("nodes", [])]
        edges = [GraphEdge.model_validate(edge) for edge in payload.get("edges", [])]
        return PlantGraph(project_id=project_id, nodes=nodes, edges=edges)

    def get_graph(self, project_id: str) -> PlantGraph:
        project_service.ensure_project(project_id)
        return self._load_graph(project_id)

    def node_details(self, project_id: str, node_id: str) -> dict[str, object]:
        graph = self._load_graph(project_id)
        node = next((item for item in graph.nodes if item.id == node_id), None)
        if node is None:
            return {"project_id": project_id, "node_id": node_id, "found": False}

        inbound = [edge.source for edge in graph.edges if edge.target == node_id]
        outbound = [edge.target for edge in graph.edges if edge.source == node_id]
        return {
            "project_id": project_id,
            "node_id": node_id,
            "found": True,
            "node": node.model_dump(),
            "inbound": inbound,
            "outbound": outbound,
        }

    def trace(self, project_id: str, node_id: str) -> TraceResponse:
        project_service.ensure_project(project_id)
        graph = self._load_graph(project_id)
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge.target)

        if node_id not in {node.id for node in graph.nodes}:
            return TraceResponse(project_id=project_id, node_id=node_id, path=[])

        queue: deque[list[str]] = deque([[node_id]])
        visited: set[str] = {node_id}
        longest_path: list[str] = [node_id]

        while queue:
            current_path = queue.popleft()
            tail = current_path[-1]
            if len(current_path) > len(longest_path):
                longest_path = current_path

            for neighbor in adjacency.get(tail, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(current_path + [neighbor])

        return TraceResponse(project_id=project_id, node_id=node_id, path=longest_path)

    def get_plant_signals(self, project_id: str) -> list[PlantSignalRow]:
        graph = self._load_graph(project_id)
        node_by_id = {node.id: node for node in graph.nodes}

        canonical_by_token: dict[str, str] = {}
        for node in graph.nodes:
            token = normalize_tag(node.id)
            current_id = canonical_by_token.get(token)
            if current_id is None:
                canonical_by_token[token] = node.id
                continue
            current = node_by_id[current_id]
            if (not node.is_synthetic and current.is_synthetic) or (node.confidence > current.confidence):
                canonical_by_token[token] = node.id

        representative_ids = set(canonical_by_token.values())
        token_for_id = {node_id: normalize_tag(node_id) for node_id in node_by_id.keys()}
        representative_for_id = {
            node_id: canonical_by_token.get(token_for_id[node_id], node_id)
            for node_id in node_by_id.keys()
        }

        controls_by_sensor: dict[str, set[str]] = defaultdict(set)
        controlling_sensors_by_target: dict[str, set[str]] = defaultdict(set)
        measures_by_sensor: dict[str, set[str]] = defaultdict(set)
        controls_process_by_actuator: dict[str, set[str]] = defaultdict(set)
        relationship_types_by_node: dict[str, set[str]] = defaultdict(set)
        relevant_neighbors: dict[str, set[str]] = defaultdict(set)
        evidence_refs_by_node: dict[str, set[str]] = defaultdict(set)
        inference_sources_by_node: dict[str, set[str]] = defaultdict(set)
        related_confidence: dict[str, list[float]] = defaultdict(list)

        for edge in graph.edges:
            source = representative_for_id.get(edge.source, edge.source)
            target = representative_for_id.get(edge.target, edge.target)
            if source == target:
                continue
            if source not in representative_ids or target not in representative_ids:
                continue

            edge_type = edge.edge_type.upper()
            relationship_types_by_node[source].add(edge_type)
            relationship_types_by_node[target].add(edge_type)
            if edge.confidence is not None:
                related_confidence[source].append(float(edge.confidence))
                related_confidence[target].append(float(edge.confidence))

            refs = [*edge.source_references, edge.explanation or "", edge.inference_source or ""]
            for ref in refs:
                if not ref:
                    continue
                evidence_refs_by_node[source].add(str(ref))
                evidence_refs_by_node[target].add(str(ref))
            if edge.inference_source:
                inference_sources_by_node[source].add(edge.inference_source.lower())
                inference_sources_by_node[target].add(edge.inference_source.lower())

            source_role = process_role_from_node(node_by_id[source].node_type if source in node_by_id else None)
            target_role = process_role_from_node(node_by_id[target].node_type if target in node_by_id else None)

            if edge_type in {"SIGNAL_TO", "CONTROLS"}:
                controls_by_sensor[source].add(target)
                controlling_sensors_by_target[target].add(source)
                relevant_neighbors[source].add(target)
                relevant_neighbors[target].add(source)
                if source_role == "actuator" and target_role == "process":
                    controls_process_by_actuator[source].add(target)
                if source_role == "process" and target_role == "actuator":
                    controls_process_by_actuator[target].add(source)
            if edge_type in {"MEASURES", "MONITORS"}:
                measures_by_sensor[source].add(target)
                relevant_neighbors[source].add(target)
                relevant_neighbors[target].add(source)
                if source_role == "process" and target_role == "sensor":
                    measures_by_sensor[target].add(source)
            if edge_type in {"CONNECTED_TO", "PROCESS_FLOW", "FEEDS", "DISCHARGES_TO", "PART_OF"}:
                relevant_neighbors[source].add(target)
                relevant_neighbors[target].add(source)

        loops: dict[str, dict[str, object]] = {}
        sensors_by_process: dict[str, set[str]] = defaultdict(set)
        actuators_by_process: dict[str, set[str]] = defaultdict(set)

        for sensor, processes in measures_by_sensor.items():
            for process in processes:
                if process_role_from_node(node_by_id[process].node_type if process in node_by_id else None) == "process":
                    sensors_by_process[process].add(sensor)

        for actuator, processes in controls_process_by_actuator.items():
            for process in processes:
                if process_role_from_node(node_by_id[process].node_type if process in node_by_id else None) == "process":
                    actuators_by_process[process].add(actuator)

        # Fallback for legacy graphs: infer sensor/actuator membership from node.process_unit when explicit
        # MEASURES/CONTROLS-to-process edges are not present yet.
        for node_id in representative_ids:
            node = node_by_id.get(node_id)
            if node is None or not node.process_unit:
                continue
            process_id = representative_for_id.get(node.process_unit, node.process_unit)
            if process_id not in representative_ids:
                continue
            role = process_role_from_node(node.node_type)
            if role == "sensor":
                sensors_by_process[process_id].add(node_id)
            elif role == "actuator":
                actuators_by_process[process_id].add(node_id)

        for process, sensors in sensors_by_process.items():
            for actuator in actuators_by_process.get(process, set()):
                for sensor in sensors:
                    loop_id = self._loop_id(sensor, actuator)
                    measure_evidence = [
                        item
                        for item in graph.edges
                        if item.edge_type.upper() in {"MEASURES", "MONITORS"}
                        and (
                            (representative_for_id.get(item.source, item.source) == sensor and representative_for_id.get(item.target, item.target) == process)
                            or (representative_for_id.get(item.target, item.target) == sensor and representative_for_id.get(item.source, item.source) == process)
                        )
                    ]
                    control_evidence = [
                        item
                        for item in graph.edges
                        if item.edge_type.upper() == "CONTROLS"
                        and (
                            (representative_for_id.get(item.source, item.source) == actuator and representative_for_id.get(item.target, item.target) == process)
                            or (representative_for_id.get(item.target, item.target) == actuator and representative_for_id.get(item.source, item.source) == process)
                        )
                    ]
                    loop_confidence = 0.7
                    if measure_evidence or control_evidence:
                        loop_confidence = (
                            sum(float(edge.confidence) for edge in [*measure_evidence, *control_evidence])
                            / max(1, len([*measure_evidence, *control_evidence]))
                        )
                    loops[loop_id] = {
                        "loop_id": loop_id,
                        "sensor": sensor,
                        "process": process,
                        "actuator": actuator,
                        "source": "INFERRED",
                        "confidence": round(min(0.99, max(0.35, loop_confidence)), 3),
                    }

        loop_ids_by_node: dict[str, set[str]] = defaultdict(set)
        control_path_by_node: dict[str, set[str]] = defaultdict(set)
        for loop_id, loop in loops.items():
            sensor = str(loop["sensor"])
            actuator = str(loop["actuator"])
            process = str(loop["process"])
            for member in (sensor, actuator, process):
                loop_ids_by_node[member].add(loop_id)
            control_path_by_node[sensor].add(f"{sensor} -> {process} -> {actuator}")
            control_path_by_node[actuator].add(f"{sensor} -> {process} -> {actuator}")
            control_path_by_node[process].add(f"{sensor} -> {process} -> {actuator}")

        for sensor, targets in controls_by_sensor.items():
            for target in targets:
                control_path_by_node[sensor].add(f"{sensor} -> {target}")
                control_path_by_node[target].add(f"{sensor} -> {target}")

        rows: list[PlantSignalRow] = []
        for node_id in sorted(representative_ids):
            node = node_by_id[node_id]
            metadata = node.metadata if isinstance(node.metadata, dict) else {}
            role = process_role_from_node(node.node_type)
            signal_type = node.signal_type or signal_type_from_tag(node_id, node.node_type)
            if signal_type == "unknown":
                signal_type = "process" if role == "process" else None

            connected_to = sorted(item for item in relevant_neighbors.get(node_id, set()) if item != node_id)
            control_targets = sorted(item for item in controls_by_sensor.get(node_id, set()) if item != node_id)
            controlling_signals = sorted(item for item in controlling_sensors_by_target.get(node_id, set()) if item != node_id)
            control_path = sorted(control_path_by_node.get(node_id, set()))
            loop_ids = sorted(loop_ids_by_node.get(node_id, set()))
            relationship_types = sorted(relationship_types_by_node.get(node_id, set()))

            raw_evidence = set(evidence_refs_by_node.get(node_id, set()))
            raw_evidence.update(str(item) for item in node.source_documents)
            raw_evidence.update(str(item) for item in node.source_references)
            evidence_text = " ".join(sorted(raw_evidence)).lower()
            has_pid = any(token in evidence_text for token in ("p&id", "pid", "diagram", ".pdf"))
            has_narrative = any(token in evidence_text for token in ("narrative", "control narrative", "starts when", "if ", "when "))
            has_inferred = bool(inference_sources_by_node.get(node_id, set()) - {"narrative"}) or "synthesis" in evidence_text or "inferred" in evidence_text

            source = "INFERRED"
            if has_pid and has_narrative:
                source = "PID+NARRATIVE"
            elif has_pid and has_inferred:
                source = "PID+INFERRED"
            elif has_narrative and has_inferred:
                source = "NARRATIVE+INFERRED"
            elif has_pid:
                source = "PID"
            elif has_narrative:
                source = "NARRATIVE"

            relation_conf = sum(related_confidence.get(node_id, [0.62])) / max(1, len(related_confidence.get(node_id, [])))
            class_conf = classification_confidence(node_id, node.node_type)
            loop_bonus = 0.08 if loop_ids else 0.0
            confidence = (0.42 * float(node.confidence or 0.65)) + (0.28 * class_conf) + (0.22 * relation_conf) + loop_bonus

            rows.append(
                PlantSignalRow(
                    tag=node_id,
                    type=node.node_type,
                    signal_type=signal_type,
                    process_unit=node.process_unit,
                    connected_to=connected_to,
                    control_targets=control_targets,
                    controlling_signals=controlling_signals,
                    control_path=control_path,
                    loop_ids=loop_ids,
                    loop_id=loop_ids[0] if loop_ids else None,
                    relationship_types=relationship_types,
                    confidence=round(min(0.99, max(0.35, confidence)), 3),
                    source=source,
                    source_details=[
                        *sorted(raw_evidence)[:6],
                        *[
                            f"{loop_id}:{loops[loop_id]['sensor']}->{loops[loop_id]['process']}->{loops[loop_id]['actuator']}:{loops[loop_id]['confidence']}"
                            for loop_id in loop_ids[:3]
                            if loop_id in loops
                        ],
                    ],
                )
            )

        return rows


graph_service = GraphService()
