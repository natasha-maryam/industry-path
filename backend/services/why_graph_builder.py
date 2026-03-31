from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


INVALID_EDGE_TAGS = {"SOURCE", "SINK", "UNCONNECTED", "UNRESOLVED"}

INFERRED_CONFIDENCE_BY_REL_TYPE: dict[str, float] = {
    "UPSTREAM": 0.8,
    "DOWNSTREAM": 0.8,
    "SIGNAL_INPUT": 0.75,
    "SIGNAL_OUTPUT": 0.75,
    "CONTROLS": 0.85,
    "CONTROLLED_BY": 0.85,
}


@dataclass
class WhyNode:
    tag: str
    node_id: str
    node_type: str
    subtype: str | None = None
    description: str | None = None
    system: str | None = None
    equipment: str | None = None
    process_role: str | None = None
    runtime: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WhyEdge:
    source: str
    target: str
    rel_type: str
    confidence: float
    source_type: str
    inferred: bool


@dataclass
class WhyGraph:
    nodes: dict[str, WhyNode]
    edges: list[WhyEdge]
    outgoing: dict[str, list[WhyEdge]]
    incoming: dict[str, list[WhyEdge]]


class WhyGraphBuilder:
    @staticmethod
    def _to_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def _is_valid_edge_endpoint(cls, value: Any) -> bool:
        text = cls._to_text(value)
        if not text:
            return False
        return text.upper() not in INVALID_EDGE_TAGS

    @staticmethod
    def _to_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                text = str(item).strip()
                if text:
                    result.append(text)
            return result
        if isinstance(value, tuple):
            result = []
            for item in value:
                text = str(item).strip()
                if text:
                    result.append(text)
            return result
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def _get_value(row: Mapping[str, Any], field: str, default: Any = None) -> Any:
        return row.get(field, default)

    def build_nodes(self, rows: Iterable[Mapping[str, Any]]) -> dict[str, WhyNode]:
        nodes: dict[str, WhyNode] = {}
        for raw_row in rows:
            tag = self._to_text(self._get_value(raw_row, "tag"))
            if not tag:
                continue

            runtime = {
                "current_value": self._get_value(raw_row, "current_value"),
                "state": self._get_value(raw_row, "state"),
                "setpoint": self._get_value(raw_row, "setpoint"),
                "mode": self._get_value(raw_row, "mode"),
                "unit": self._get_value(raw_row, "unit"),
            }

            metadata = {
                "confidence": self._get_value(raw_row, "confidence", 0.0),
                "warnings": list(self._to_list(self._get_value(raw_row, "warnings", []))),
                "grounded_fields": dict(self._get_value(raw_row, "grounded_fields", {}) or {}),
                "derived_fields": dict(self._get_value(raw_row, "derived_fields", {}) or {}),
                "traceability": list(self._get_value(raw_row, "traceability", []) or []),
                "document_source": list(self._to_list(self._get_value(raw_row, "document_source", []))),
                "line_reference": list(self._to_list(self._get_value(raw_row, "line_reference", []))),
                "num_connections": self._get_value(raw_row, "num_connections", 0),
                "num_upstream": self._get_value(raw_row, "num_upstream", 0),
                "num_downstream": self._get_value(raw_row, "num_downstream", 0),
                "is_orphan": bool(self._get_value(raw_row, "is_orphan", False)),
                "is_controlled": bool(self._get_value(raw_row, "is_controlled", False)),
                "is_actuated": bool(self._get_value(raw_row, "is_actuated", False)),
            }

            nodes[tag] = WhyNode(
                tag=tag,
                node_id=self._to_text(self._get_value(raw_row, "id", tag)) or tag,
                node_type=self._to_text(self._get_value(raw_row, "type", "unknown")) or "unknown",
                subtype=self._get_value(raw_row, "subtype"),
                description=self._get_value(raw_row, "description"),
                system=self._get_value(raw_row, "system"),
                equipment=self._get_value(raw_row, "equipment"),
                process_role=self._get_value(raw_row, "process_role"),
                runtime=runtime,
                metadata=metadata,
            )

        return nodes

    def build_edges(
        self,
        rows: Iterable[Mapping[str, Any]],
        explicit_edges: Iterable[Mapping[str, Any]] | None = None,
    ) -> tuple[list[WhyEdge], dict[str, list[WhyEdge]], dict[str, list[WhyEdge]]]:
        edge_by_key: dict[tuple[str, str, str], WhyEdge] = {}
        normalized_rows = list(rows)

        def add_edge(edge: WhyEdge) -> None:
            if not self._is_valid_edge_endpoint(edge.source) or not self._is_valid_edge_endpoint(edge.target):
                return
            if edge.source == edge.target and edge.inferred:
                return

            key = (edge.source, edge.target, edge.rel_type)
            current = edge_by_key.get(key)
            if current is None:
                edge_by_key[key] = edge
                return

            if current.inferred and not edge.inferred:
                edge_by_key[key] = edge
                return

            if edge.confidence > current.confidence:
                edge_by_key[key] = edge

        if explicit_edges:
            for raw_edge in explicit_edges:
                source = self._to_text(raw_edge.get("source"))
                target = self._to_text(raw_edge.get("target"))
                rel_type = self._to_text(raw_edge.get("edge_type") or raw_edge.get("type") or "RELATED_TO") or "RELATED_TO"
                confidence_raw = raw_edge.get("confidence")
                confidence = float(confidence_raw) if confidence_raw is not None else 1.0
                source_type = self._to_text(raw_edge.get("source_type") or "explicit") or "explicit"
                add_edge(
                    WhyEdge(
                        source=source,
                        target=target,
                        rel_type=rel_type,
                        confidence=confidence,
                        source_type=source_type,
                        inferred=False,
                    )
                )

        inferred_fields: tuple[tuple[str, str, str], ...] = (
            ("upstream", "UPSTREAM", "source_to_row"),
            ("downstream", "DOWNSTREAM", "row_to_target"),
            ("signal_inputs", "SIGNAL_INPUT", "source_to_row"),
            ("signal_outputs", "SIGNAL_OUTPUT", "row_to_target"),
            ("controls", "CONTROLS", "row_to_target"),
            ("controlled_by", "CONTROLLED_BY", "source_to_row"),
        )

        for row in normalized_rows:
            row_tag = self._to_text(row.get("tag"))
            if not self._is_valid_edge_endpoint(row_tag):
                continue

            for field_name, rel_type, direction in inferred_fields:
                for candidate in self._to_list(row.get(field_name, [])):
                    if direction == "source_to_row":
                        source = candidate
                        target = row_tag
                    else:
                        source = row_tag
                        target = candidate

                    add_edge(
                        WhyEdge(
                            source=source,
                            target=target,
                            rel_type=rel_type,
                            confidence=INFERRED_CONFIDENCE_BY_REL_TYPE.get(rel_type, 0.75),
                            source_type=f"row:{field_name}",
                            inferred=True,
                        )
                    )

        edges = sorted(edge_by_key.values(), key=lambda item: (item.source, item.target, item.rel_type))
        outgoing: dict[str, list[WhyEdge]] = defaultdict(list)
        incoming: dict[str, list[WhyEdge]] = defaultdict(list)
        for edge in edges:
            outgoing[edge.source].append(edge)
            incoming[edge.target].append(edge)

        return edges, dict(outgoing), dict(incoming)

    def build_graph(
        self,
        rows: Iterable[Mapping[str, Any]],
        explicit_edges: Iterable[Mapping[str, Any]] | None = None,
    ) -> WhyGraph:
        normalized_rows = [dict(row) for row in rows]
        nodes = self.build_nodes(normalized_rows)
        edges, outgoing, incoming = self.build_edges(normalized_rows, explicit_edges=explicit_edges)
        return WhyGraph(nodes=nodes, edges=edges, outgoing=outgoing, incoming=incoming)
