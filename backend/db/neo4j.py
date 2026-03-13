import os
from dataclasses import dataclass

from neo4j import GraphDatabase


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str


class Neo4jClient:
    def __init__(self) -> None:
        self.config = Neo4jConfig(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
        )
        self.driver = GraphDatabase.driver(self.config.uri, auth=(self.config.user, self.config.password))

    def clear_project_graph(self, project_id: str) -> None:
        query = """
        MATCH (n {project_id: $project_id})
        DETACH DELETE n
        """
        with self.driver.session() as session:
            session.run(query, project_id=project_id)

    def write_project_graph(self, project_id: str, nodes: list[dict], edges: list[dict]) -> None:
        with self.driver.session() as session:
            for node in nodes:
                query = """
                MERGE (n:Device {project_id: $project_id, id: $id})
                SET n.label = $label,
                    n.node_type = $node_type,
                    n.status = $status,
                    n.description = $description,
                    n.source_documents = $source_documents,
                    n.signals = $signals,
                    n.alarms = $alarms,
                    n.interlocks = $interlocks,
                    n.mode = $mode,
                    n.linked_logic = $linked_logic,
                    n.process_unit = $process_unit,
                    n.cluster_id = $cluster_id,
                    n.cluster_name = $cluster_name,
                    n.cluster_order = $cluster_order,
                    n.node_rank = $node_rank,
                    n.preferred_direction = $preferred_direction,
                    n.confidence = $confidence,
                    n.is_synthetic = $is_synthetic,
                    n.explanation = $explanation,
                    n.source_references = $source_references,
                    n.equipment_type = $equipment_type,
                    n.signal_type = $signal_type,
                    n.instrument_role = $instrument_role,
                    n.control_role = $control_role,
                    n.power_rating = $power_rating,
                    n.connected_to = $connected_to,
                    n.controls = $controls,
                    n.measures = $measures,
                    n.control_path = $control_path,
                    n.metadata = $metadata,
                    n.metadata_confidence = $metadata_confidence
                """
                session.run(
                    query,
                    project_id=project_id,
                    id=node["id"],
                    label=node["label"],
                    node_type=node["node_type"],
                    status=node.get("status", "unknown"),
                    description=node.get("description"),
                    source_documents=node.get("source_documents", []),
                    signals=node.get("signals", []),
                    alarms=node.get("alarms", []),
                    interlocks=node.get("interlocks", []),
                    mode=node.get("mode"),
                    linked_logic=node.get("linked_logic", []),
                    process_unit=node.get("process_unit"),
                    cluster_id=node.get("cluster_id"),
                    cluster_name=node.get("cluster_name"),
                    cluster_order=node.get("cluster_order"),
                    node_rank=node.get("node_rank"),
                    preferred_direction=node.get("preferred_direction"),
                    confidence=node.get("confidence", 0.8),
                    is_synthetic=node.get("is_synthetic", False),
                    explanation=node.get("explanation"),
                    source_references=node.get("source_references", []),
                    equipment_type=node.get("equipment_type"),
                    signal_type=node.get("signal_type"),
                    instrument_role=node.get("instrument_role"),
                    control_role=node.get("control_role"),
                    power_rating=node.get("power_rating"),
                    connected_to=node.get("connected_to", []),
                    controls=node.get("controls", []),
                    measures=node.get("measures", []),
                    control_path=node.get("control_path", []),
                    metadata=node.get("metadata", {}),
                    metadata_confidence=node.get("metadata_confidence", {}),
                )

            for edge in edges:
                relation = edge["edge_type"].upper().replace("-", "_")
                relation = relation if relation.isidentifier() else "CONNECTED_TO"
                query = f"""
                MATCH (a:Device {{project_id: $project_id, id: $source}})
                MATCH (b:Device {{project_id: $project_id, id: $target}})
                MERGE (a)-[r:{relation} {{project_id: $project_id, id: $id}}]->(b)
                SET r.edge_type = $edge_type,
                    r.edge_class = $edge_class,
                    r.line_style = $line_style,
                    r.confidence = $confidence,
                    r.explanation = $explanation,
                    r.inference_source = $inference_source,
                    r.source_references = $source_references,
                    r.edge_label = $edge_label,
                    r.semantic_kind = $semantic_kind,
                    r.process_flow_direction = $process_flow_direction
                """
                session.run(
                    query,
                    project_id=project_id,
                    id=edge["id"],
                    source=edge["source"],
                    target=edge["target"],
                    edge_type=edge["edge_type"],
                    edge_class=edge.get("edge_class", "process"),
                    line_style=edge.get("line_style", "solid"),
                    confidence=edge.get("confidence", 0.7),
                    explanation=edge.get("explanation"),
                    inference_source=edge.get("inference_source"),
                    source_references=edge.get("source_references", []),
                    edge_label=edge.get("edge_label"),
                    semantic_kind=edge.get("semantic_kind"),
                    process_flow_direction=edge.get("process_flow_direction"),
                )

    def fetch_project_graph(self, project_id: str) -> tuple[list[dict], list[dict]]:
        node_query = """
        MATCH (n:Device {project_id: $project_id})
         RETURN n.id AS id,
             n.label AS label,
             n.node_type AS node_type,
             n.status AS status,
             n.description AS description,
             coalesce(n.source_documents, []) AS source_documents,
             coalesce(n.signals, []) AS signals,
             coalesce(n.alarms, []) AS alarms,
             coalesce(n.interlocks, []) AS interlocks,
             n.mode AS mode,
               coalesce(n.linked_logic, []) AS linked_logic,
               n.process_unit AS process_unit,
               n.cluster_id AS cluster_id,
               n.cluster_name AS cluster_name,
               n.cluster_order AS cluster_order,
               n.node_rank AS node_rank,
               n.preferred_direction AS preferred_direction,
               coalesce(n.confidence, 0.8) AS confidence,
               coalesce(n.is_synthetic, false) AS is_synthetic,
               n.explanation AS explanation,
               coalesce(n.source_references, []) AS source_references,
               n.equipment_type AS equipment_type,
               n.signal_type AS signal_type,
               n.instrument_role AS instrument_role,
               n.control_role AS control_role,
               n.power_rating AS power_rating,
               coalesce(n.connected_to, []) AS connected_to,
               coalesce(n.controls, []) AS controls,
               coalesce(n.measures, []) AS measures,
               coalesce(n.control_path, []) AS control_path,
               coalesce(n.metadata, {}) AS metadata,
               coalesce(n.metadata_confidence, {}) AS metadata_confidence
        """
        edge_query = """
        MATCH (a:Device {project_id: $project_id})-[r]->(b:Device {project_id: $project_id})
           RETURN r.id AS id,
                a.id AS source,
                b.id AS target,
                r.edge_type AS edge_type,
                coalesce(r.edge_class, 'process') AS edge_class,
                coalesce(r.line_style, 'solid') AS line_style,
                coalesce(r.confidence, 0.7) AS confidence,
                r.explanation AS explanation,
                r.inference_source AS inference_source,
                coalesce(r.source_references, []) AS source_references,
                r.edge_label AS edge_label,
                r.semantic_kind AS semantic_kind,
                r.process_flow_direction AS process_flow_direction
        """
        with self.driver.session() as session:
            nodes = [dict(row) for row in session.run(node_query, project_id=project_id)]
            edges = [dict(row) for row in session.run(edge_query, project_id=project_id)]
        return nodes, edges

    def health(self) -> dict[str, str]:
        status = "connected"
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as exc:
            status = f"error: {exc}"

        return {
            "backend": "neo4j",
            "uri": self.config.uri,
            "status": status,
        }


neo4j_client = Neo4jClient()
