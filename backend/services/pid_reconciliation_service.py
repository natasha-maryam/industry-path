from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from fastapi import HTTPException

from models.graph import GraphEdge, GraphNode, PlantGraph
from models.pid_reconciliation import (
    PIDApplyUpdateResponse,
    PIDChangeEntry,
    PIDConflict,
    PIDReconcileSummary,
    PIDTopologyChange,
)
from models.pipeline import ConfidenceLevel, EngineeringEntity, InferredRelationship
from services.engineering_validator import engineering_validator
from services.graph_service import graph_service
from services.graph_validation_service import graph_validation_service
from services.project_service import project_service


@dataclass(frozen=True)
class _NormalizedRecord:
    tag: str
    label: str
    node_type: str
    status: str
    process_unit: str | None
    connected_to: tuple[str, ...]
    controls: tuple[str, ...]
    measures: tuple[str, ...]


class PIDReconciliationService:
    def __init__(self) -> None:
        self._prefix_by_type: dict[str, str] = {
            "pump": "P",
            "valve": "XV",
            "control_valve": "CV",
            "flow_transmitter": "FT",
            "level_transmitter": "LT",
            "level_switch": "LS",
            "pressure_transmitter": "PT",
            "differential_pressure_transmitter": "PDT",
            "analyzer": "AIT",
            "blower": "B",
            "tank": "TK",
            "basin": "BS",
            "clarifier": "CL",
            "chemical_system_device": "CH",
            "generic_device": "DEV",
        }

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _paths(self, project_id: str):
        return project_service.workspace_paths(project_id)

    @staticmethod
    def _state_path(paths) -> Path:
        return paths.monitoring / "pid_changes_latest.json"

    @staticmethod
    def _proposed_graph_path(paths) -> Path:
        return paths.monitoring / "pid_proposed_graph.json"

    def _resolve_project_id(self, project_id: str | None = None) -> str:
        if project_id:
            project_service.ensure_project(project_id)
            return project_id
        active = project_service.get_active_project()
        if active is None:
            raise HTTPException(status_code=404, detail="No active project selected")
        return str(active.id)

    def _normalize_tag(self, raw: str, node_type: str | None = None) -> str:
        cleaned = (raw or "").upper().strip()
        cleaned = re.sub(r"\s+", "", cleaned)
        cleaned = cleaned.replace("_", "-")
        cleaned = re.sub(r"-+", "-", cleaned)

        if not cleaned:
            return ""

        alpha_num = re.fullmatch(r"([A-Z]+)-?(\d+[A-Z0-9]*)", cleaned)
        if alpha_num:
            prefix, suffix = alpha_num.group(1), alpha_num.group(2)
            return f"{prefix}-{suffix}"

        if re.fullmatch(r"\d+[A-Z0-9]*", cleaned):
            inferred_prefix = self._prefix_by_type.get((node_type or "").lower(), "DEV")
            return f"{inferred_prefix}-{cleaned}"

        if "-" not in cleaned:
            split = re.match(r"^([A-Z]{1,5})(\d+.*)$", cleaned)
            if split:
                return f"{split.group(1)}-{split.group(2)}"

        return cleaned

    def _normalize_records(self, records: list[dict[str, object]]) -> tuple[list[_NormalizedRecord], list[PIDConflict]]:
        normalized: list[_NormalizedRecord] = []
        collisions: dict[str, list[str]] = {}

        for item in records:
            raw_tag = str(item.get("tag") or "")
            node_type = str(item.get("node_type") or "generic_device")
            tag = self._normalize_tag(raw_tag, node_type=node_type)
            if not tag:
                continue
            collisions.setdefault(tag, []).append(raw_tag)
            normalized.append(
                _NormalizedRecord(
                    tag=tag,
                    label=str(item.get("label") or tag),
                    node_type=node_type,
                    status=str(item.get("status") or "healthy"),
                    process_unit=(str(item.get("process_unit")) if item.get("process_unit") else None),
                    connected_to=tuple(self._normalize_tag(str(x), node_type=None) for x in (item.get("connected_to") or [])),
                    controls=tuple(self._normalize_tag(str(x), node_type=None) for x in (item.get("controls") or [])),
                    measures=tuple(self._normalize_tag(str(x), node_type=None) for x in (item.get("measures") or [])),
                )
            )

        conflicts: list[PIDConflict] = []
        for normalized_tag, raw_values in collisions.items():
            unique_raw = sorted({value for value in raw_values if value})
            if len(unique_raw) <= 1:
                continue
            for raw_value in unique_raw:
                conflicts.append(
                    PIDConflict(
                        incoming_tag=raw_value,
                        existing_tag=normalized_tag,
                        similarity=1.0,
                        reason="Multiple raw tags normalized to the same canonical tag",
                    )
                )

        return normalized, conflicts

    def _build_edges_from_records(self, records: list[_NormalizedRecord]) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        seen_ids: set[str] = set()

        def add_edge(source: str, target: str, edge_type: str) -> None:
            if not source or not target or source == target:
                return
            edge_id = f"{edge_type}:{source}:{target}"
            if edge_id in seen_ids:
                return
            seen_ids.add(edge_id)
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=source,
                    target=target,
                    edge_type=edge_type,
                    edge_class="process",
                    line_style="solid",
                    confidence=0.85,
                    explanation="P&ID reconciliation inferred edge",
                    inference_source="validation",
                    source_references=["pid-reconciliation"],
                )
            )

        for item in records:
            for target in item.connected_to:
                add_edge(item.tag, target, "CONNECTED_TO")
            for target in item.controls:
                add_edge(item.tag, target, "CONTROLS")
            for target in item.measures:
                add_edge(item.tag, target, "MEASURES")

        return edges

    def _to_entity(self, node: GraphNode) -> EngineeringEntity:
        canonical = str(node.node_type or "generic_device").lower()
        allowed = {
            "pump",
            "valve",
            "control_valve",
            "flow_transmitter",
            "level_transmitter",
            "level_switch",
            "pressure_transmitter",
            "differential_pressure_transmitter",
            "analyzer",
            "blower",
            "tank",
            "basin",
            "clarifier",
            "chemical_system_device",
            "generic_device",
            "process_unit",
        }
        canonical_type = canonical if canonical in allowed else "generic_device"
        return EngineeringEntity(
            id=node.id,
            tag=node.id,
            canonical_type=canonical_type,  # type: ignore[arg-type]
            display_name=node.label,
            process_unit=node.process_unit,
            source_documents=node.source_documents,
            source_pages=[],
            source_snippets=[],
            confidence=float(node.confidence or 0.8),
            is_synthetic=node.is_synthetic,
            explanation=node.explanation,
            source_references=node.source_references,
            parse_notes=["pid_reconciliation"],
        )

    @staticmethod
    def _confidence_level(score: float) -> ConfidenceLevel:
        if score >= 0.8:
            return "HIGH"
        if score >= 0.6:
            return "MEDIUM"
        return "LOW"

    def _to_relationship(self, edge: GraphEdge) -> InferredRelationship | None:
        relationship_type = edge.edge_type.upper()
        allowed = {
            "PROCESS_FLOW",
            "CONNECTED_TO",
            "FEEDS",
            "DISCHARGES_TO",
            "SUPPLIES_AIR_TO",
            "MEASURES",
            "CONTROLS",
            "SIGNAL_TO",
            "PART_OF",
            "MONITORS",
            "INTERLOCKS_WITH",
            "ALARMS_ON",
            "SUPPORTS",
            "LOCATED_IN",
            "ASSOCIATED_WITH",
        }
        if relationship_type not in allowed:
            return None
        score = float(edge.confidence or 0.7)
        return InferredRelationship(
            relationship_type=relationship_type,  # type: ignore[arg-type]
            source_entity=edge.source,
            target_entity=edge.target,
            confidence_score=score,
            confidence_level=self._confidence_level(score),
            inference_source="validation",
            explanation=edge.explanation or "P&ID reconciliation candidate",
            source_references=edge.source_references,
        )

    def _edge_key(self, edge: GraphEdge) -> tuple[str, str, str]:
        return (edge.source.upper(), edge.target.upper(), edge.edge_type.upper())

    def _persist_reconcile_state(
        self,
        project_id: str,
        summary: PIDReconcileSummary,
        proposed_graph: PlantGraph,
    ) -> None:
        paths = self._paths(project_id)
        state_path = self._state_path(paths)
        proposal_path = self._proposed_graph_path(paths)
        state_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
        proposal_path.write_text(proposed_graph.model_dump_json(indent=2), encoding="utf-8")

    def _load_reconcile_state(self, project_id: str) -> tuple[PIDReconcileSummary | None, PlantGraph | None]:
        paths = self._paths(project_id)
        state_path = self._state_path(paths)
        proposal_path = self._proposed_graph_path(paths)
        summary = PIDReconcileSummary.model_validate_json(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
        proposed = PlantGraph.model_validate_json(proposal_path.read_text(encoding="utf-8")) if proposal_path.exists() else None
        return summary, proposed

    def reconcile(
        self,
        dataset: list[dict[str, object]],
        similarity_threshold: float = 0.9,
        project_id: str | None = None,
    ) -> PIDReconcileSummary:
        resolved_project_id = self._resolve_project_id(project_id)
        current_graph = graph_service.get_graph(resolved_project_id)

        normalized_records, normalization_conflicts = self._normalize_records(dataset)
        incoming_map = {record.tag: record for record in normalized_records}
        current_map = {self._normalize_tag(node.id, node.node_type): node for node in current_graph.nodes}

        new_tags = sorted(set(incoming_map.keys()) - set(current_map.keys()))
        deprecated_tags = sorted(set(current_map.keys()) - set(incoming_map.keys()))

        new_devices = [
            PIDChangeEntry(tag=tag, details=f"New device from normalized dataset ({incoming_map[tag].node_type})")
            for tag in new_tags
        ]
        deprecated_devices = [
            PIDChangeEntry(tag=tag, details="Device not present in incoming normalized dataset (kept as deprecated)")
            for tag in deprecated_tags
        ]

        similarity_conflicts: list[PIDConflict] = []
        existing_tags = sorted(current_map.keys())
        for incoming_tag in sorted(incoming_map.keys()):
            for existing_tag in existing_tags:
                if incoming_tag == existing_tag:
                    continue
                score = SequenceMatcher(a=incoming_tag, b=existing_tag).ratio()
                if score >= similarity_threshold:
                    similarity_conflicts.append(
                        PIDConflict(
                            incoming_tag=incoming_tag,
                            existing_tag=existing_tag,
                            similarity=round(score, 4),
                            reason="Tag similarity exceeded configured threshold",
                        )
                    )

        possible_conflicts = [*normalization_conflicts, *similarity_conflicts]

        proposed_nodes: dict[str, GraphNode] = {
            self._normalize_tag(node.id, node.node_type): copy.deepcopy(node)
            for node in current_graph.nodes
        }

        for tag in deprecated_tags:
            node = proposed_nodes.get(tag)
            if not node:
                continue
            node.status = "deprecated"
            metadata = dict(node.metadata)
            metadata["deprecated"] = True
            metadata["deprecated_at"] = self._now().isoformat()
            node.metadata = metadata

        for tag, item in incoming_map.items():
            existing = proposed_nodes.get(tag)
            if existing:
                existing.label = item.label
                existing.node_type = item.node_type
                existing.status = "healthy"
                existing.process_unit = item.process_unit
                existing.connected_to = sorted(set(existing.connected_to) | set(item.connected_to))
                existing.controls = sorted(set(existing.controls) | set(item.controls))
                existing.measures = sorted(set(existing.measures) | set(item.measures))
            else:
                proposed_nodes[tag] = GraphNode(
                    id=tag,
                    label=item.label,
                    node_type=item.node_type,
                    status=item.status,
                    process_unit=item.process_unit,
                    connected_to=list(item.connected_to),
                    controls=list(item.controls),
                    measures=list(item.measures),
                    source_references=["pid_reconciliation"],
                    confidence=0.85,
                )

        incoming_edges = self._build_edges_from_records(list(incoming_map.values()))
        current_edge_map = {self._edge_key(edge): edge for edge in current_graph.edges}
        incoming_edge_map = {self._edge_key(edge): edge for edge in incoming_edges}

        topology_changes: list[PIDTopologyChange] = []
        for key, edge in incoming_edge_map.items():
            if key not in current_edge_map:
                topology_changes.append(
                    PIDTopologyChange(
                        edge_id=edge.id,
                        source=edge.source,
                        target=edge.target,
                        edge_type=edge.edge_type,
                        change="added",
                    )
                )
        for key, edge in current_edge_map.items():
            if key not in incoming_edge_map:
                topology_changes.append(
                    PIDTopologyChange(
                        edge_id=edge.id,
                        source=edge.source,
                        target=edge.target,
                        edge_type=edge.edge_type,
                        change="removed",
                    )
                )

        proposed_edges = list(incoming_edge_map.values())
        proposed_graph = PlantGraph(
            project_id=resolved_project_id,
            nodes=list(proposed_nodes.values()),
            edges=proposed_edges,
        )

        summary = PIDReconcileSummary(
            project_id=resolved_project_id,
            generated_at=self._now(),
            similarity_threshold=similarity_threshold,
            new_devices=new_devices,
            deprecated_devices=deprecated_devices,
            topology_changes=topology_changes,
            possible_conflicts=possible_conflicts,
            apply_ready=len(possible_conflicts) == 0,
        )

        self._persist_reconcile_state(resolved_project_id, summary, proposed_graph)
        return summary

    def reconcile_from_entities(
        self,
        project_id: str,
        entities: list[EngineeringEntity],
        relationships: list[InferredRelationship],
        similarity_threshold: float = 0.9,
    ) -> PIDReconcileSummary:
        dataset: list[dict[str, object]] = []
        controls_by_source: dict[str, list[str]] = {}
        measures_by_source: dict[str, list[str]] = {}
        connected_by_source: dict[str, list[str]] = {}

        for rel in relationships:
            if rel.relationship_type == "CONTROLS":
                controls_by_source.setdefault(rel.source_entity, []).append(rel.target_entity)
            elif rel.relationship_type == "MEASURES":
                measures_by_source.setdefault(rel.source_entity, []).append(rel.target_entity)
            elif rel.relationship_type in {"CONNECTED_TO", "PROCESS_FLOW", "FEEDS", "DISCHARGES_TO"}:
                connected_by_source.setdefault(rel.source_entity, []).append(rel.target_entity)

        for entity in entities:
            dataset.append(
                {
                    "tag": entity.id,
                    "label": entity.display_name,
                    "node_type": entity.canonical_type,
                    "status": "healthy",
                    "process_unit": entity.process_unit,
                    "connected_to": connected_by_source.get(entity.id, []),
                    "controls": controls_by_source.get(entity.id, []),
                    "measures": measures_by_source.get(entity.id, []),
                }
            )

        return self.reconcile(
            dataset=dataset,
            similarity_threshold=similarity_threshold,
            project_id=project_id,
        )

    def get_changes(self, project_id: str | None = None) -> PIDReconcileSummary:
        resolved_project_id = self._resolve_project_id(project_id)
        summary, _ = self._load_reconcile_state(resolved_project_id)
        if summary is None:
            return PIDReconcileSummary(
                project_id=resolved_project_id,
                generated_at=self._now(),
                similarity_threshold=0.9,
                new_devices=[],
                deprecated_devices=[],
                topology_changes=[],
                possible_conflicts=[],
                apply_ready=False,
            )
        return summary

    def apply_update(
        self,
        allow_conflicts: bool = False,
        force_apply_on_validation_warnings: bool = False,
        project_id: str | None = None,
    ) -> PIDApplyUpdateResponse:
        resolved_project_id = self._resolve_project_id(project_id)
        summary, proposed = self._load_reconcile_state(resolved_project_id)
        if summary is None or proposed is None:
            raise HTTPException(status_code=400, detail="No pending reconciliation changes. Run /pid/reconcile first.")

        if summary.possible_conflicts and not allow_conflicts:
            raise HTTPException(status_code=409, detail="Conflicts detected. Resolve/review conflicts or set allow_conflicts=true.")

        entities = [self._to_entity(node) for node in proposed.nodes]
        relationships = [rel for rel in (self._to_relationship(edge) for edge in proposed.edges) if rel is not None]

        accepted_relationships, validation_warnings, low_relationships = graph_validation_service.validate(
            entities=entities,
            relationships=relationships,
        )

        validation_report = engineering_validator.validate(resolved_project_id, entities)
        validation_failed = validation_report.status == "failed"

        if validation_failed and not force_apply_on_validation_warnings:
            raise HTTPException(
                status_code=400,
                detail=f"Engineering validation failed with {len(validation_report.errors)} errors before apply.",
            )

        accepted_edges = [
            GraphEdge(
                id=f"{rel.relationship_type}:{rel.source_entity}:{rel.target_entity}",
                source=rel.source_entity,
                target=rel.target_entity,
                edge_type=rel.relationship_type,
                confidence=rel.confidence_score,
                explanation=rel.explanation,
                inference_source=rel.inference_source,
                source_references=rel.source_references,
            )
            for rel in accepted_relationships
        ]

        result_graph = PlantGraph(project_id=resolved_project_id, nodes=proposed.nodes, edges=accepted_edges)
        graph_service.store_graph(
            resolved_project_id,
            [node.model_dump(mode="json") for node in result_graph.nodes],
            [edge.model_dump(mode="json") for edge in result_graph.edges],
        )

        note = {
            "applied_at": self._now().isoformat(),
            "validation_status": validation_report.status,
            "validation_errors": [item.model_dump(mode="json") for item in validation_report.errors],
            "validation_warnings": [item.model_dump(mode="json") for item in validation_report.warnings],
            "graph_validation_warnings": [item.model_dump(mode="json") for item in validation_warnings],
            "low_confidence_relationships": [item.model_dump(mode="json") for item in low_relationships],
            "accepted_edges": len(accepted_edges),
        }
        paths = self._paths(resolved_project_id)
        (paths.monitoring / "pid_apply_report.json").write_text(json.dumps(note, indent=2), encoding="utf-8")

        return PIDApplyUpdateResponse(
            project_id=resolved_project_id,
            applied_at=self._now(),
            nodes_count=len(result_graph.nodes),
            edges_count=len(result_graph.edges),
            validation_status=validation_report.status,
            commit_triggered=True,
            summary="P&ID reconciliation update applied safely to plant graph.",
        )


pid_reconciliation_service = PIDReconciliationService()
