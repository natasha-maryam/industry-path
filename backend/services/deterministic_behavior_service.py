from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Callable, Iterable, Mapping

from models.engineering_table import EngineeringTableRow
from models.graph import GraphEdge
from services.why_chain_resolver import WhyChainResolver
from services.why_engine_hardened import WhyEngineHardened
from services.why_graph_builder import WhyGraphBuilder
from services.why_narrative_engine import WhyNarrativeEngine


BehaviorListener = Callable[[str, dict[str, Any]], None]
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeState:
    tag: str
    current_value: str | None = None
    state: str | None = None
    setpoint: str | None = None
    mode: str | None = None
    unit: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    snapshot_id: str = "snapshot-00000000"
    revision: int = 0

    def apply_patch(self, patch: Mapping[str, Any], snapshot_id: str) -> bool:
        changed = False

        def to_string_or_none(value: Any) -> str | None:
            if value is None:
                return None
            text = str(value).strip()
            return text or None

        for key in ("current_value", "state", "setpoint", "mode", "unit"):
            if key not in patch:
                continue
            next_value = to_string_or_none(patch.get(key))
            if getattr(self, key) != next_value:
                setattr(self, key, next_value)
                changed = True

        if changed:
            self.snapshot_id = snapshot_id
            self.revision += 1
            self.updated_at = datetime.now(timezone.utc).isoformat()

        return changed

    def as_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "current_value": self.current_value,
            "state": self.state,
            "setpoint": self.setpoint,
            "mode": self.mode,
            "unit": self.unit,
            "updated_at": self.updated_at,
            "snapshot_id": self.snapshot_id,
            "revision": self.revision,
        }


@dataclass(slots=True, frozen=True)
class RelationshipEdge:
    id: str
    source: str
    target: str
    edge_type: str
    edge_class: str | None = None
    confidence: float | None = None
    source_type: str = "explicit"
    inferred: bool = False


@dataclass(slots=True)
class RowModel:
    id: str
    tag: str
    type: str
    subtype: str | None = None
    description: str | None = None
    system: str | None = None
    equipment: str | None = None
    process_role: str | None = None
    measures: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    controlled_by: list[str] = field(default_factory=list)
    signal_inputs: list[str] = field(default_factory=list)
    signal_outputs: list[str] = field(default_factory=list)
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    flow_path: list[str] = field(default_factory=list)
    current_value: str | None = None
    state: str | None = None
    setpoint: str | None = None
    mode: str | None = None
    unit: str | None = None
    range_min: float | None = None
    range_max: float | None = None
    fail_state: str | None = None
    power: str | None = None
    document_source: list[str] = field(default_factory=list)
    line_reference: list[str] = field(default_factory=list)
    confidence: float = 0.0
    num_connections: int = 0
    num_upstream: int = 0
    num_downstream: int = 0
    control_chain: list[str] = field(default_factory=list)
    flow_chain: list[str] = field(default_factory=list)
    is_orphan: bool = False
    is_controlled: bool = False
    is_actuated: bool = False
    warnings: list[str] = field(default_factory=list)
    grounded_fields: dict[str, object] = field(default_factory=dict)
    derived_fields: dict[str, object] = field(default_factory=dict)
    traceability: list[dict[str, Any]] = field(default_factory=list)

    behavior_card: str = ""
    behavior_summary: str = ""
    cause_chain: list[str] = field(default_factory=list)
    effect_chain: list[str] = field(default_factory=list)
    impact_summary: str = ""
    behavior_confidence: float = 0.0
    state_snapshot_id: str = "snapshot-00000000"
    why_trace_available: bool = False

    @classmethod
    def from_engineering_row(cls, row: EngineeringTableRow | Mapping[str, Any], snapshot_id: str) -> "RowModel":
        def get_value(field_name: str, default: Any = None) -> Any:
            if isinstance(row, Mapping):
                return row.get(field_name, default)
            return getattr(row, field_name, default)

        traceability_items: list[dict[str, Any]] = []
        raw_traceability = get_value("traceability", []) or []
        for item in raw_traceability:
            if hasattr(item, "model_dump"):
                traceability_items.append(item.model_dump())
            elif isinstance(item, Mapping):
                traceability_items.append(dict(item))

        return cls(
            id=str(get_value("id", "")).strip(),
            tag=str(get_value("tag", "")).strip(),
            type=str(get_value("type", "unknown")).strip() or "unknown",
            subtype=get_value("subtype"),
            description=get_value("description"),
            system=get_value("system"),
            equipment=get_value("equipment"),
            process_role=get_value("process_role"),
            measures=[str(item) for item in (get_value("measures", []) or []) if item],
            controls=[str(item) for item in (get_value("controls", []) or []) if item],
            controlled_by=[str(item) for item in (get_value("controlled_by", []) or []) if item],
            signal_inputs=[str(item) for item in (get_value("signal_inputs", []) or []) if item],
            signal_outputs=[str(item) for item in (get_value("signal_outputs", []) or []) if item],
            upstream=[str(item) for item in (get_value("upstream", []) or []) if item],
            downstream=[str(item) for item in (get_value("downstream", []) or []) if item],
            flow_path=[str(item) for item in (get_value("flow_path", []) or []) if item],
            current_value=(str(get_value("current_value")).strip() if get_value("current_value") is not None else None),
            state=(str(get_value("state")).strip() if get_value("state") is not None else None),
            setpoint=(str(get_value("setpoint")).strip() if get_value("setpoint") is not None else None),
            mode=(str(get_value("mode")).strip() if get_value("mode") is not None else None),
            unit=(str(get_value("unit")).strip() if get_value("unit") is not None else None),
            range_min=get_value("range_min"),
            range_max=get_value("range_max"),
            fail_state=get_value("fail_state"),
            power=get_value("power"),
            document_source=[str(item) for item in (get_value("document_source", []) or []) if item],
            line_reference=[str(item) for item in (get_value("line_reference", []) or []) if item],
            confidence=float(get_value("confidence", 0.0) or 0.0),
            num_connections=int(get_value("num_connections", 0) or 0),
            num_upstream=int(get_value("num_upstream", 0) or 0),
            num_downstream=int(get_value("num_downstream", 0) or 0),
            control_chain=[str(item) for item in (get_value("control_chain", []) or []) if item],
            flow_chain=[str(item) for item in (get_value("flow_chain", []) or []) if item],
            is_orphan=bool(get_value("is_orphan", False)),
            is_controlled=bool(get_value("is_controlled", False)),
            is_actuated=bool(get_value("is_actuated", False)),
            warnings=[str(item) for item in (get_value("warnings", []) or []) if item],
            grounded_fields=dict(get_value("grounded_fields", {}) or {}),
            derived_fields=dict(get_value("derived_fields", {}) or {}),
            traceability=traceability_items,
            state_snapshot_id=snapshot_id,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tag": self.tag,
            "type": self.type,
            "subtype": self.subtype,
            "description": self.description,
            "system": self.system,
            "equipment": self.equipment,
            "process_role": self.process_role,
            "measures": list(self.measures),
            "controls": list(self.controls),
            "controlled_by": list(self.controlled_by),
            "signal_inputs": list(self.signal_inputs),
            "signal_outputs": list(self.signal_outputs),
            "upstream": list(self.upstream),
            "downstream": list(self.downstream),
            "flow_path": list(self.flow_path),
            "current_value": self.current_value,
            "state": self.state,
            "setpoint": self.setpoint,
            "mode": self.mode,
            "unit": self.unit,
            "range_min": self.range_min,
            "range_max": self.range_max,
            "fail_state": self.fail_state,
            "power": self.power,
            "document_source": list(self.document_source),
            "line_reference": list(self.line_reference),
            "confidence": self.confidence,
            "num_connections": self.num_connections,
            "num_upstream": self.num_upstream,
            "num_downstream": self.num_downstream,
            "control_chain": list(self.control_chain),
            "flow_chain": list(self.flow_chain),
            "is_orphan": self.is_orphan,
            "is_controlled": self.is_controlled,
            "is_actuated": self.is_actuated,
            "warnings": list(self.warnings),
            "grounded_fields": dict(self.grounded_fields),
            "derived_fields": dict(self.derived_fields),
            "traceability": [dict(item) for item in self.traceability],
            "behavior_card": self.behavior_card,
            "behavior_summary": self.behavior_summary,
            "cause_chain": list(self.cause_chain),
            "effect_chain": list(self.effect_chain),
            "impact_summary": self.impact_summary,
            "behavior_confidence": self.behavior_confidence,
            "state_snapshot_id": self.state_snapshot_id,
            "why_trace_available": self.why_trace_available,
        }


class DeterministicBehaviorService:
    def __init__(self, impact_radius: int = 2, default_chain_depth: int = 4) -> None:
        self._lock = RLock()
        self._impact_radius = max(1, impact_radius)
        self._default_chain_depth = max(1, default_chain_depth)
        self._why_narrative_engine = WhyNarrativeEngine()
        self._why_engine_hardened = WhyEngineHardened()

        self._rows_by_tag: dict[str, RowModel] = {}
        self._runtime_by_tag: dict[str, RuntimeState] = {}
        self._edges: list[RelationshipEdge] = []

        self._outbound: dict[str, set[str]] = defaultdict(set)
        self._inbound: dict[str, set[str]] = defaultdict(set)
        self._neighbor_index: dict[str, set[str]] = defaultdict(set)
        self._edge_type_pairs: dict[tuple[str, str], str] = {}

        self._listeners: dict[str, BehaviorListener] = {}
        self._listener_sequence = 0
        self._snapshot_sequence = 0
        self._active_snapshot_id = self._next_snapshot_id_locked()

    @staticmethod
    def normalize_tag(tag: str) -> str:
        raw = str(tag or "").strip().upper()
        if not raw:
            return ""
        compact = "".join(ch for ch in raw if ch.isalnum())
        return compact

    @classmethod
    def tags_match(cls, left: str, right: str) -> bool:
        return bool(cls.normalize_tag(left)) and cls.normalize_tag(left) == cls.normalize_tag(right)

    def resolve_row_tag(self, tag: str) -> str | None:
        normalized = self.normalize_tag(tag)
        if not normalized:
            return None
        with self._lock:
            for row_tag in self._rows_by_tag.keys():
                if self.normalize_tag(row_tag) == normalized:
                    return row_tag
        return None

    def register_listener(self, callback: BehaviorListener) -> str:
        with self._lock:
            self._listener_sequence += 1
            listener_id = f"listener-{self._listener_sequence:06d}"
            self._listeners[listener_id] = callback
            return listener_id

    def unregister_listener(self, listener_id: str) -> None:
        with self._lock:
            self._listeners.pop(listener_id, None)

    def get_listener_count(self) -> int:
        with self._lock:
            return len(self._listeners)

    def get_rows_loaded_count(self) -> int:
        with self._lock:
            return len(self._rows_by_tag)

    def has_row_tag(self, tag: str) -> bool:
        with self._lock:
            if tag in self._rows_by_tag:
                return True
            normalized = self.normalize_tag(tag)
            if not normalized:
                return False
            return any(self.normalize_tag(row_tag) == normalized for row_tag in self._rows_by_tag.keys())

    def has_runtime_tag(self, tag: str) -> bool:
        with self._lock:
            if tag in self._runtime_by_tag:
                return True
            normalized = self.normalize_tag(tag)
            if not normalized:
                return False
            return any(self.normalize_tag(runtime_tag) == normalized for runtime_tag in self._runtime_by_tag.keys())

    def get_row_preview(self, tag: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._rows_by_tag.get(tag)
            if row is None:
                return None
            return row.as_dict()

    def get_sample_tags(self, limit: int = 10) -> list[str]:
        with self._lock:
            effective_limit = max(0, limit)
            return sorted(self._rows_by_tag.keys())[:effective_limit]

    def get_runtime_values_count(self) -> int:
        with self._lock:
            return len(self._runtime_by_tag)

    def get_edges(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "edge_class": edge.edge_class,
                    "confidence": edge.confidence,
                    "source_type": edge.source_type,
                    "inferred": edge.inferred,
                }
                for edge in self._edges
            ]

    def load(
        self,
        rows: Iterable[EngineeringTableRow | Mapping[str, Any]],
        edges: Iterable[GraphEdge | RelationshipEdge | Mapping[str, Any]],
        runtime_seed: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        listeners: list[BehaviorListener]
        payload: dict[str, Any]
        with self._lock:
            self._rows_by_tag.clear()
            self._runtime_by_tag.clear()
            self._active_snapshot_id = self._next_snapshot_id_locked()

            normalized_rows: list[dict[str, Any]] = []
            explicit_edge_payloads: list[dict[str, Any]] = []
            for raw_edge in edges:
                if hasattr(raw_edge, "model_dump"):
                    explicit_edge_payloads.append(dict(raw_edge.model_dump()))
                elif isinstance(raw_edge, Mapping):
                    explicit_edge_payloads.append(dict(raw_edge))
                else:
                    explicit_edge_payloads.append(
                        {
                            "id": getattr(raw_edge, "id", ""),
                            "source": getattr(raw_edge, "source", ""),
                            "target": getattr(raw_edge, "target", ""),
                            "edge_type": getattr(raw_edge, "edge_type", "RELATED_TO"),
                            "edge_class": getattr(raw_edge, "edge_class", None),
                            "confidence": getattr(raw_edge, "confidence", None),
                        }
                    )

            for raw_row in rows:
                row = RowModel.from_engineering_row(raw_row, snapshot_id=self._active_snapshot_id)
                if not row.tag:
                    continue
                self._rows_by_tag[row.tag] = row
                normalized_rows.append(row.as_dict())
                self._runtime_by_tag[row.tag] = RuntimeState(
                    tag=row.tag,
                    current_value=row.current_value,
                    state=row.state,
                    setpoint=row.setpoint,
                    mode=row.mode,
                    unit=row.unit,
                    snapshot_id=self._active_snapshot_id,
                )

            graph_builder = WhyGraphBuilder()
            graph = graph_builder.build_graph(normalized_rows, explicit_edges=explicit_edge_payloads)
            self._edges = [
                RelationshipEdge(
                    id=f"edge-{index:08d}",
                    source=edge.source,
                    target=edge.target,
                    edge_type=edge.rel_type,
                    edge_class=("inferred" if edge.inferred else "explicit"),
                    confidence=edge.confidence,
                    source_type=edge.source_type,
                    inferred=edge.inferred,
                )
                for index, edge in enumerate(graph.edges, start=1)
            ]
            self._rebuild_edge_indexes_locked()

            if runtime_seed:
                for tag, patch in runtime_seed.items():
                    state = self._runtime_by_tag.get(tag)
                    if state is None:
                        continue
                    state.apply_patch(patch, snapshot_id=self._active_snapshot_id)

            recomputed = self._recompute_rows_locked(set(self._rows_by_tag.keys()), self._active_snapshot_id)
            payload = {
                "snapshot_id": self._active_snapshot_id,
                "rows_loaded": len(self._rows_by_tag),
                "edges_loaded": len(self._edges),
                "recomputed": len(recomputed),
            }
            listeners = list(self._listeners.values())

        self._notify_listeners(listeners, "loaded", payload)
        return payload

    def get_row(self, tag: str) -> RowModel | None:
        with self._lock:
            row = self._rows_by_tag.get(tag)
            if row is None:
                return None
            return RowModel(**row.as_dict())

    def get_rows(self, tags: Iterable[str] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if tags is None:
                target_tags = sorted(self._rows_by_tag.keys())
            else:
                target_tags = [tag for tag in tags if tag in self._rows_by_tag]
            return [self._rows_by_tag[tag].as_dict() for tag in target_tags]

    def get_runtime_state(self, tag: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._runtime_by_tag.get(tag)
            return state.as_dict() if state else None

    def update_runtime_values(
        self,
        updates: Mapping[str, Mapping[str, Any]],
        radius: int | None = None,
    ) -> dict[str, Any]:
        listeners: list[BehaviorListener]
        payload: dict[str, Any]
        with self._lock:
            changed_tags: set[str] = set()
            ignored_tags: list[str] = []
            unknown_tags: list[str] = []
            tag_remap: dict[str, str] = {}

            if not updates:
                logger.info("behavior_runtime_update skipped empty_updates")
                return {
                    "snapshot_id": self._active_snapshot_id,
                    "changed_tags": [],
                    "impacted_tags": [],
                    "updated_rows": [],
                    "ignored_tags": [],
                    "unknown_tags": [],
                    "tag_remap": {},
                    "debug": {
                        "requested_tags": [],
                        "normalized_requested_tags": [],
                        "known_row_tags": len(self._rows_by_tag),
                        "known_runtime_tags": len(self._runtime_by_tag),
                    },
                }

            next_snapshot_id = self._next_snapshot_id_locked()

            def to_string_or_none(value: Any) -> str | None:
                if value is None:
                    return None
                text = str(value).strip()
                return text or None

            for incoming_tag, patch in updates.items():
                resolved_tag = incoming_tag if incoming_tag in self._rows_by_tag else None
                if resolved_tag is None:
                    incoming_normalized = self.normalize_tag(incoming_tag)
                    if incoming_normalized:
                        for known_tag in self._rows_by_tag.keys():
                            if self.normalize_tag(known_tag) == incoming_normalized:
                                resolved_tag = known_tag
                                if known_tag != incoming_tag:
                                    tag_remap[incoming_tag] = known_tag
                                break

                if resolved_tag is None:
                    ignored_tags.append(incoming_tag)
                    unknown_tags.append(incoming_tag)
                    continue

                changed_tags.add(resolved_tag)
                state = self._runtime_by_tag.get(resolved_tag)
                if state is None:
                    state = RuntimeState(tag=resolved_tag, snapshot_id=next_snapshot_id)
                    self._runtime_by_tag[resolved_tag] = state

                state.apply_patch(patch, snapshot_id=next_snapshot_id)

                row = self._rows_by_tag.get(resolved_tag)
                if row is not None:
                    if "current_value" in patch:
                        row.current_value = to_string_or_none(patch.get("current_value"))
                    if "state" in patch:
                        row.state = to_string_or_none(patch.get("state"))
                    if "setpoint" in patch:
                        row.setpoint = to_string_or_none(patch.get("setpoint"))
                    if "mode" in patch:
                        row.mode = to_string_or_none(patch.get("mode"))

            if not changed_tags:
                self._active_snapshot_id = next_snapshot_id
                logger.info(
                    "behavior_runtime_update no_matching_rows updates=%s ignored=%s",
                    sorted(updates.keys()),
                    sorted(ignored_tags),
                )
                return {
                    "snapshot_id": self._active_snapshot_id,
                    "changed_tags": [],
                    "impacted_tags": [],
                    "updated_rows": [],
                    "ignored_tags": ignored_tags,
                    "unknown_tags": sorted(unknown_tags),
                    "tag_remap": dict(tag_remap),
                    "debug": {
                        "requested_tags": sorted(updates.keys()),
                        "normalized_requested_tags": sorted({self.normalize_tag(tag) for tag in updates.keys() if self.normalize_tag(tag)}),
                        "known_row_tags": len(self._rows_by_tag),
                        "known_runtime_tags": len(self._runtime_by_tag),
                    },
                }

            self._active_snapshot_id = next_snapshot_id
            impacted_tags = self._expand_radius_locked(changed_tags, radius if radius is not None else self._impact_radius)
            updated_row_tags = self._recompute_rows_locked(impacted_tags, self._active_snapshot_id)
            updated_rows = [self._rows_by_tag[tag].as_dict() for tag in updated_row_tags if tag in self._rows_by_tag]

            payload = {
                "snapshot_id": self._active_snapshot_id,
                "changed_tags": sorted(changed_tags),
                "impacted_tags": sorted(impacted_tags),
                "updated_rows": updated_rows,
                "ignored_tags": sorted(ignored_tags),
                "unknown_tags": sorted(unknown_tags),
                "tag_remap": dict(tag_remap),
                "debug": {
                    "requested_tags": sorted(updates.keys()),
                    "normalized_requested_tags": sorted({self.normalize_tag(tag) for tag in updates.keys() if self.normalize_tag(tag)}),
                    "known_row_tags": len(self._rows_by_tag),
                    "known_runtime_tags": len(self._runtime_by_tag),
                },
            }
            listeners = list(self._listeners.values())

            logger.info(
                "behavior_runtime_update updated changed_tags=%s impacted_tags=%s ignored_tags=%s unknown_tags=%s remapped=%s updated_rows=%s",
                payload["changed_tags"],
                payload["impacted_tags"],
                payload["ignored_tags"],
                payload["unknown_tags"],
                payload["tag_remap"],
                len(updated_rows),
            )

        self._notify_listeners(listeners, "runtime_update", payload)
        return payload

    def explain_why(self, tag: str, max_depth: int = 3) -> dict[str, Any]:
        with self._lock:
            requested_tag = str(tag or "").strip()
            normalized_requested_tag = self.normalize_tag(requested_tag)
            row = self._rows_by_tag.get(requested_tag)

            hardened_rows = [item.as_dict() for item in self._rows_by_tag.values()]
            hardened_edges = [
                {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "edge_class": edge.edge_class,
                    "confidence": edge.confidence,
                    "source_type": edge.source_type,
                    "inferred": edge.inferred,
                }
                for edge in self._edges
            ]
            hardened_output = self._why_engine_hardened.generate(
                requested_tag,
                hardened_rows,
                edges=hardened_edges,
                version="v1",
            )
            hardened_structure = dict(hardened_output.get("structure") or {})
            hardened_explanation = dict(hardened_output.get("explanation") or {})
            hardened_debug = dict(hardened_output.get("debug") or {})

            logger.info(
                "[WHY_CHAIN_DEBUG] engine_selected_tag raw=%s normalized=%s",
                requested_tag,
                normalized_requested_tag,
            )
            if row is None:
                exists_by_normalized = any(self.normalize_tag(row_tag) == normalized_requested_tag for row_tag in self._rows_by_tag.keys())
                missing_reason = "normalized_key_mismatch" if exists_by_normalized else "selected_tag_absent"
                narrative = self._why_narrative_engine.build(
                    target_tag=requested_tag,
                    target_role="unknown",
                    target_type=None,
                    target_subtype=None,
                    behavior_summary=None,
                    ranked_upstream=[],
                    ranked_downstream=[],
                    runtime_state=None,
                    diagnostics_reason=missing_reason,
                )
                logger.info(
                    "[WHY_CHAIN_DEBUG] selected_tag_exists_in_nodes=%s total_nodes=%s total_edges=%s",
                    False,
                    len(self._rows_by_tag),
                    len(self._edges),
                )
                explanation = hardened_explanation if hardened_explanation else narrative
                return {
                    "tag": requested_tag,
                    "available": False,
                    "snapshot_id": self._active_snapshot_id,
                    "steps": [],
                    "debug": {
                        "classification": {
                            "selected_tag_role": "unknown",
                            "selected_tag_role_reason": "tag_not_found",
                            "classification_inputs": {},
                        },
                        "graph": {
                            "selected_tag": tag,
                            "incoming_edge_count": 0,
                            "outgoing_edge_count": 0,
                            "normalized_upstream_tags": [],
                            "normalized_downstream_tags": [],
                        },
                        "edges": [],
                        "neighbors": [],
                        "chain_diagnostics": {
                            "requested_tag": requested_tag,
                            "normalized_requested_tag": normalized_requested_tag,
                            "exists_in_nodes": False,
                            "exists_by_normalized_key": exists_by_normalized,
                            "reason": missing_reason,
                            "resolver_called": False,
                            "upstream_candidate_paths": 0,
                            "downstream_candidate_paths": 0,
                            "ranked_upstream_returned": 0,
                            "ranked_downstream_returned": 0,
                        },
                    },
                    "structure": (hardened_structure or {
                        "ranked_upstream": [],
                        "ranked_downstream": [],
                        "merged_context": {
                            "parallel_upstream": [],
                            "parallel_downstream": [],
                        },
                        "diagnostics": {
                            "reason": missing_reason,
                            "ranked_upstream_count": 0,
                            "ranked_downstream_count": 0,
                        },
                    }),
                    "engine": hardened_debug,
                    "explanation": explanation,
                    "narrative": explanation,
                }

            steps = self._build_why_trace_locked(requested_tag, max_depth=max(1, max_depth))
            runtime_state = self._runtime_by_tag.get(requested_tag)
            debug = self._build_why_debug_locked(requested_tag)
            chain_resolution = dict((hardened_structure.get("chains") or {}) if hardened_structure else {})
            if not chain_resolution:
                chain_resolution = self._resolve_ranked_chains_locked(requested_tag, max_depth=max(1, max_depth))
            else:
                chain_resolution.setdefault("diagnostics", {})
                chain_resolution["diagnostics"]["hardened_engine"] = True
                chain_resolution["diagnostics"]["cache_hit"] = bool(hardened_debug.get("cache_hit", False))

            debug["chains"] = chain_resolution
            debug["chain_diagnostics"] = dict(chain_resolution.get("diagnostics", {}) or {})
            structure = hardened_structure if hardened_structure else self._build_why_structure_locked(chain_resolution)
            steps = self._build_why_trace_locked(requested_tag, max_depth=max(1, max_depth), chain_resolution=chain_resolution)
            narrative = self._why_narrative_engine.build(
                target_tag=requested_tag,
                target_role=str(debug.get("classification", {}).get("selected_tag_role") or "unknown"),
                target_type=row.type,
                target_subtype=row.subtype,
                behavior_summary=row.behavior_summary,
                ranked_upstream=(hardened_structure.get("ranked_upstream", []) if hardened_structure else structure.get("ranked_upstream", [])) or [],
                ranked_downstream=(hardened_structure.get("ranked_downstream", []) if hardened_structure else structure.get("ranked_downstream", [])) or [],
                runtime_state=runtime_state.as_dict() if runtime_state else None,
                diagnostics_reason=str(((hardened_structure.get("diagnostics", {}) if hardened_structure else structure.get("diagnostics", {})) or {}).get("reason") or ""),
            )
            explanation = hardened_explanation if hardened_explanation else narrative
            logger.info(
                "[WHY_NARRATIVE_DEBUG] tag=%s summary_len=%s behavior_len=%s upstream_len=%s downstream_len=%s state_len=%s warnings_count=%s",
                requested_tag,
                len(str(explanation.get("summary", "") or "")),
                len(str(explanation.get("behavior", "") or "")),
                len(str(explanation.get("upstream", "") or "")),
                len(str(explanation.get("downstream", "") or "")),
                len(str(explanation.get("state", "") or "")),
                len(list(explanation.get("warnings", []) or [])),
            )

            logger.info(
                "[WHY_DEBUG] selected_tag=%s role=%s in_edges=%s out_edges=%s upstream=%s downstream=%s",
                requested_tag,
                debug.get("classification", {}).get("selected_tag_role", "unknown"),
                debug.get("graph", {}).get("incoming_edge_count", 0),
                debug.get("graph", {}).get("outgoing_edge_count", 0),
                ",".join(debug.get("graph", {}).get("normalized_upstream_tags", [])),
                ",".join(debug.get("graph", {}).get("normalized_downstream_tags", [])),
            )

            logger.info(
                "[WHY_DEBUG] selected_tag=%s ranked_upstream=%s ranked_downstream=%s merged_context=%s",
                requested_tag,
                len(chain_resolution.get("ranked_upstream", [])),
                len(chain_resolution.get("ranked_downstream", [])),
                len((chain_resolution.get("merged_context", {}) or {}).get("parallel_context_tags", [])),
            )
            logger.info(
                "[WHY_CHAIN_DEBUG] serialized_structure_lengths upstream=%s downstream=%s final_api_response_tag=%s",
                len((structure.get("ranked_upstream", []) or [])),
                len((structure.get("ranked_downstream", []) or [])),
                requested_tag,
            )

            return {
                "tag": requested_tag,
                "available": row.why_trace_available,
                "snapshot_id": row.state_snapshot_id,
                "behavior_card": row.behavior_card,
                "behavior_summary": row.behavior_summary,
                "runtime_state": runtime_state.as_dict() if runtime_state else None,
                "steps": steps,
                "debug": debug,
                "structure": structure,
                "engine": hardened_debug,
                "explanation": explanation,
                "narrative": explanation,
            }

    def _build_why_structure_locked(self, chain_resolution: Mapping[str, Any] | None) -> dict[str, Any]:
        source = dict(chain_resolution or {})
        ranked_upstream = source.get("ranked_upstream", []) or []
        ranked_downstream = source.get("ranked_downstream", []) or []
        merged_context = source.get("merged_context", {}) or {}
        diagnostics = source.get("diagnostics", {}) or {}

        def normalize_ranked_chain(item: Mapping[str, Any]) -> dict[str, Any]:
            tags = [str(tag).strip() for tag in (item.get("nodes", []) or []) if str(tag).strip()]
            weak_links = list(item.get("weak_links", []) or [])
            broken = bool(item.get("broken", False))
            break_reason_raw = str(item.get("break_reason", "")).strip()
            break_reason = break_reason_raw if broken and break_reason_raw else None

            score_raw = item.get("score")
            try:
                score = float(score_raw)
            except (TypeError, ValueError):
                score = 0.0

            return {
                "tags": tags,
                "score": round(score, 6),
                "depth": max(0, len(tags) - 1),
                "weak_links": weak_links,
                "broken": broken,
                "break_reason": break_reason,
            }

        return {
            "ranked_upstream": [normalize_ranked_chain(item) for item in ranked_upstream if isinstance(item, Mapping)],
            "ranked_downstream": [normalize_ranked_chain(item) for item in ranked_downstream if isinstance(item, Mapping)],
            "merged_context": {
                "parallel_upstream": [
                    str(tag).strip()
                    for tag in (merged_context.get("parallel_upstream_tags", []) or [])
                    if str(tag).strip()
                ],
                "parallel_downstream": [
                    str(tag).strip()
                    for tag in (merged_context.get("parallel_downstream_tags", []) or [])
                    if str(tag).strip()
                ],
            },
            "diagnostics": {
                "reason": str(diagnostics.get("zero_reason", "") or ""),
                "ranked_upstream_count": len([item for item in ranked_upstream if isinstance(item, Mapping)]),
                "ranked_downstream_count": len([item for item in ranked_downstream if isinstance(item, Mapping)]),
            },
        }

    @staticmethod
    def _normalize_source_type(source_type: str | None, inferred: bool) -> str:
        raw = str(source_type or "").strip().lower()
        if inferred:
            if raw.startswith("row:"):
                raw = raw.split(":", 1)[1]
            if raw in {"upstream", "downstream", "controls", "signal_inputs", "signal_outputs", "controlled_by"}:
                return raw
        return "explicit"

    def _classify_why_role_locked(self, row: RowModel) -> tuple[str, str]:
        tag_text = (row.tag or "").strip().upper()
        type_text = (row.type or "").strip().lower()
        subtype_text = (row.subtype or "").strip().lower()
        role_text = (row.process_role or "").strip().lower()
        desc_text = (row.description or "").strip().lower()
        equipment_text = (row.equipment or "").strip().lower()

        internal_suffixes = ("_SP", "_HH", "_LL", "_ALM", "_CMD", "_STATUS")
        if tag_text.endswith(internal_suffixes):
            for suffix in internal_suffixes:
                if tag_text.endswith(suffix):
                    return "internal_logical", f"matched tag suffix {suffix} -> internal_logical"

        sensor_prefixes = ("AIT", "FIT", "LIT", "PIT", "DPIT")
        for prefix in sensor_prefixes:
            if tag_text.startswith(prefix):
                return "sensor", f"matched tag prefix {prefix} -> sensor"
        if any(token in subtype_text for token in ("transmitter", "analyzer", "sensor")):
            if "transmitter" in subtype_text:
                return "sensor", "matched subtype contains transmitter -> sensor"
            if "analyzer" in subtype_text:
                return "sensor", "matched subtype contains analyzer -> sensor"
            return "sensor", "matched subtype contains sensor -> sensor"
        if "instrument" in type_text:
            return "sensor", "matched type contains instrument -> sensor"

        actuator_prefixes = ("FCV", "VAL", "PMP", "BL", "MOTOR")
        for prefix in actuator_prefixes:
            if tag_text.startswith(prefix):
                return "actuator", f"matched tag prefix {prefix} -> actuator"
        if any(token in subtype_text for token in ("valve", "pump", "actuator", "blower")):
            if "valve" in subtype_text:
                return "actuator", "matched subtype contains valve -> actuator"
            if "pump" in subtype_text:
                return "actuator", "matched subtype contains pump -> actuator"
            if "actuator" in subtype_text:
                return "actuator", "matched subtype contains actuator -> actuator"
            return "actuator", "matched subtype contains blower -> actuator"
        if "actuator" in type_text:
            return "actuator", "matched type contains actuator -> actuator"

        if any(token in tag_text for token in ("CTRL", "LOOP", "PID", "DT_LOOP")):
            return "controller", "matched tag contains CTRL/LOOP/PID/DT_LOOP -> controller"
        if "control" in subtype_text or "control" in role_text:
            return "controller", "matched subtype/process_role contains control -> controller"

        if "process" in subtype_text:
            return "process_unit", "matched subtype=process -> process_unit"
        if "process_unit" in type_text:
            return "process_unit", "matched type contains process_unit -> process_unit"
        if any(token in equipment_text for token in ("basin", "tank", "clarifier", "reactor", "area")):
            if "basin" in equipment_text:
                return "process_unit", "matched equipment contains basin -> process_unit"
            if "tank" in equipment_text:
                return "process_unit", "matched equipment contains tank -> process_unit"
            if "clarifier" in equipment_text:
                return "process_unit", "matched equipment contains clarifier -> process_unit"
            if "reactor" in equipment_text:
                return "process_unit", "matched equipment contains reactor -> process_unit"
            return "process_unit", "matched equipment contains area -> process_unit"
        if any(token in tag_text for token in ("BAS", "TANK", "AREA")):
            if "BAS" in tag_text:
                return "process_unit", "matched tag contains BAS -> process_unit"
            if "TANK" in tag_text:
                return "process_unit", "matched tag contains TANK -> process_unit"
            return "process_unit", "matched tag contains AREA -> process_unit"

        if any(token in equipment_text for token in ("pipe", "skid", "package", "structure")):
            if "pipe" in equipment_text:
                return "passive_equipment", "matched equipment contains pipe -> passive_equipment"
            if "skid" in equipment_text:
                return "passive_equipment", "matched equipment contains skid -> passive_equipment"
            if "package" in equipment_text:
                return "passive_equipment", "matched equipment contains package -> passive_equipment"
            return "passive_equipment", "matched equipment contains structure -> passive_equipment"
        if subtype_text in {"n/a", "passive"}:
            return "passive_equipment", f"matched subtype={subtype_text} -> passive_equipment"

        if "process" in desc_text:
            return "process_unit", "matched description contains process -> process_unit"

        return "unknown", "no classification rule matched -> unknown"

    def _build_why_debug_locked(self, tag: str) -> dict[str, Any]:
        row = self._rows_by_tag.get(tag)
        if row is None:
            return {
                "classification": {
                    "selected_tag_role": "unknown",
                    "selected_tag_role_reason": "tag_not_found",
                    "classification_inputs": {},
                },
                "graph": {
                    "selected_tag": tag,
                    "incoming_edge_count": 0,
                    "outgoing_edge_count": 0,
                    "normalized_upstream_tags": [],
                    "normalized_downstream_tags": [],
                },
                "edges": [],
                "neighbors": [],
            }

        selected_role, role_reason = self._classify_why_role_locked(row)

        incoming_edges = [edge for edge in self._edges if edge.target == tag]
        outgoing_edges = [edge for edge in self._edges if edge.source == tag]
        connected_edges = incoming_edges + outgoing_edges

        upstream_neighbors = sorted({edge.source for edge in incoming_edges if edge.source})
        downstream_neighbors = sorted({edge.target for edge in outgoing_edges if edge.target})
        immediate_neighbors = sorted(set(upstream_neighbors) | set(downstream_neighbors))

        edge_debug = [
            {
                "source": edge.source,
                "target": edge.target,
                "rel_type": edge.edge_type,
                "confidence": edge.confidence if edge.confidence is not None else 1.0,
                "inferred": bool(edge.inferred),
                "source_type": self._normalize_source_type(edge.source_type, bool(edge.inferred)),
            }
            for edge in connected_edges
        ]
        edge_debug.sort(key=lambda item: (item["source"], item["target"], item["rel_type"]))

        neighbors: list[dict[str, Any]] = []
        for neighbor_tag in immediate_neighbors:
            neighbor_row = self._rows_by_tag.get(neighbor_tag)
            if neighbor_row is None:
                neighbors.append(
                    {
                        "tag": neighbor_tag,
                        "role": "unknown",
                        "type": None,
                        "subtype": None,
                    }
                )
                continue

            neighbor_role, _ = self._classify_why_role_locked(neighbor_row)
            neighbors.append(
                {
                    "tag": neighbor_tag,
                    "role": neighbor_role,
                    "type": neighbor_row.type,
                    "subtype": neighbor_row.subtype,
                }
            )

        return {
            "classification": {
                "selected_tag_role": selected_role,
                "selected_tag_role_reason": role_reason,
                "classification_inputs": {
                    "type": row.type,
                    "subtype": row.subtype,
                    "description": row.description,
                    "equipment": row.equipment,
                    "system": row.system,
                    "process_role": row.process_role,
                },
            },
            "graph": {
                "selected_tag": tag,
                "incoming_edge_count": len(incoming_edges),
                "outgoing_edge_count": len(outgoing_edges),
                "normalized_upstream_tags": sorted({self.normalize_tag(item) for item in upstream_neighbors if self.normalize_tag(item)}),
                "normalized_downstream_tags": sorted({self.normalize_tag(item) for item in downstream_neighbors if self.normalize_tag(item)}),
            },
            "edges": edge_debug,
            "neighbors": neighbors,
        }

    def _notify_listeners(self, listeners: list[BehaviorListener], event_type: str, payload: dict[str, Any]) -> None:
        for listener in listeners:
            try:
                listener(event_type, payload)
            except Exception:
                continue

    def _next_snapshot_id_locked(self) -> str:
        self._snapshot_sequence += 1
        return f"snapshot-{self._snapshot_sequence:08d}"

    def _coerce_edge(self, edge: GraphEdge | RelationshipEdge | Mapping[str, Any]) -> RelationshipEdge:
        if isinstance(edge, RelationshipEdge):
            return edge
        if hasattr(edge, "model_dump"):
            payload = edge.model_dump()
        elif isinstance(edge, Mapping):
            payload = dict(edge)
        else:
            payload = {
                "id": getattr(edge, "id", ""),
                "source": getattr(edge, "source", ""),
                "target": getattr(edge, "target", ""),
                "edge_type": getattr(edge, "edge_type", "RELATED_TO"),
                "edge_class": getattr(edge, "edge_class", None),
                "confidence": getattr(edge, "confidence", None),
            }

        return RelationshipEdge(
            id=str(payload.get("id", "")).strip(),
            source=str(payload.get("source", "")).strip(),
            target=str(payload.get("target", "")).strip(),
            edge_type=str(payload.get("edge_type") or payload.get("type") or "RELATED_TO").strip() or "RELATED_TO",
            edge_class=(str(payload.get("edge_class")).strip() if payload.get("edge_class") is not None else None),
            confidence=(float(payload["confidence"]) if payload.get("confidence") is not None else None),
            source_type=(str(payload.get("source_type")).strip() if payload.get("source_type") is not None else "explicit"),
            inferred=bool(payload.get("inferred", False)),
        )

    def _rebuild_edge_indexes_locked(self) -> None:
        self._outbound.clear()
        self._inbound.clear()
        self._neighbor_index.clear()
        self._edge_type_pairs.clear()

        for edge in self._edges:
            if not edge.source or not edge.target:
                continue
            self._outbound[edge.source].add(edge.target)
            self._inbound[edge.target].add(edge.source)
            self._neighbor_index[edge.source].add(edge.target)
            self._neighbor_index[edge.target].add(edge.source)
            self._edge_type_pairs[(edge.source, edge.target)] = edge.edge_type

    def _expand_radius_locked(self, changed_tags: set[str], radius: int) -> set[str]:
        effective_radius = max(0, radius)
        impacted: set[str] = set(changed_tags)
        queue: deque[tuple[str, int]] = deque((tag, 0) for tag in sorted(changed_tags))

        while queue:
            current, depth = queue.popleft()
            if depth >= effective_radius:
                continue
            for neighbor in sorted(self._neighbor_index.get(current, set())):
                if neighbor in impacted:
                    continue
                impacted.add(neighbor)
                queue.append((neighbor, depth + 1))

        return impacted

    def _recompute_rows_locked(self, tags: set[str], snapshot_id: str) -> list[str]:
        updated_tags: list[str] = []
        for tag in sorted(tags):
            row = self._rows_by_tag.get(tag)
            if row is None:
                continue

            runtime = self._runtime_by_tag.get(tag)
            cause_chain = self._compute_chain_locked(tag, direction="upstream", max_depth=self._default_chain_depth)
            effect_chain = self._compute_chain_locked(tag, direction="downstream", max_depth=self._default_chain_depth)

            row.current_value = runtime.current_value if runtime else row.current_value
            row.state = runtime.state if runtime else row.state
            row.setpoint = runtime.setpoint if runtime else row.setpoint
            row.mode = runtime.mode if runtime else row.mode
            row.unit = runtime.unit if runtime else row.unit

            row.cause_chain = cause_chain
            row.effect_chain = effect_chain
            row.behavior_card = self._build_behavior_card_locked(row, runtime)
            row.behavior_summary = self._build_behavior_summary_locked(row, runtime, cause_chain, effect_chain)
            row.impact_summary = self._build_impact_summary_locked(cause_chain, effect_chain)
            row.behavior_confidence = self._compute_behavior_confidence_locked(row, runtime, cause_chain, effect_chain)
            row.state_snapshot_id = snapshot_id
            row.why_trace_available = bool(cause_chain or effect_chain)
            updated_tags.append(tag)

        return updated_tags

    def _compute_chain_locked(self, tag: str, direction: str, max_depth: int) -> list[str]:
        if direction not in {"upstream", "downstream"}:
            raise ValueError("direction must be 'upstream' or 'downstream'")

        adjacency = self._inbound if direction == "upstream" else self._outbound
        visited: set[str] = {tag}
        chain: list[str] = []
        queue: deque[tuple[str, int]] = deque([(tag, 0)])

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for neighbor in sorted(adjacency.get(current, set())):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                chain.append(neighbor)
                queue.append((neighbor, depth + 1))

        return chain

    def _build_node_phrase_locked(self, row: RowModel, runtime: RuntimeState | None) -> str:
        role = (row.process_role or row.type or "equipment").strip().lower()

        if role in {"sensor", "instrument"}:
            target = row.measures[0] if row.measures else (row.downstream[0] if row.downstream else "process")
            value = runtime.current_value if runtime and runtime.current_value else "latest value"
            return f"Instrument {row.tag} measures {target} at {value}."

        if role in {"controller", "control"}:
            target = row.controls[0] if row.controls else (row.downstream[0] if row.downstream else "controlled targets")
            mode = runtime.mode if runtime and runtime.mode else "auto"
            return f"Control node {row.tag} regulates {target} in {mode} mode."

        if role in {"actuator", "valve", "pump"} or row.is_actuated:
            target = row.controls[0] if row.controls else (row.downstream[0] if row.downstream else "process path")
            state = runtime.state if runtime and runtime.state else "standby"
            return f"Actuator {row.tag} drives {target} with state {state}."

        neighborhood = len(self._neighbor_index.get(row.tag, set()))
        return f"Equipment {row.tag} interacts with {neighborhood} connected node(s)."

    def _build_behavior_card_locked(self, row: RowModel, runtime: RuntimeState | None) -> str:
        phrase = self._build_node_phrase_locked(row, runtime)
        if runtime is None:
            return f"{phrase} Runtime feed pending."

        runtime_parts = [
            f"state={runtime.state}" if runtime.state else None,
            f"value={runtime.current_value}" if runtime.current_value else None,
            f"setpoint={runtime.setpoint}" if runtime.setpoint else None,
        ]
        rendered = ", ".join(part for part in runtime_parts if part)
        return f"{phrase} {rendered}".strip()

    def _build_behavior_summary_locked(
        self,
        row: RowModel,
        runtime: RuntimeState | None,
        cause_chain: list[str],
        effect_chain: list[str],
    ) -> str:
        phrase = self._build_node_phrase_locked(row, runtime)
        cause_text = ", ".join(cause_chain[:3]) if cause_chain else "none"
        effect_text = ", ".join(effect_chain[:3]) if effect_chain else "none"

        runtime_text_parts = [
            f"current={runtime.current_value}" if runtime and runtime.current_value else None,
            f"state={runtime.state}" if runtime and runtime.state else None,
            f"mode={runtime.mode}" if runtime and runtime.mode else None,
        ]
        runtime_text = ", ".join(part for part in runtime_text_parts if part) or "runtime partial"

        return f"{phrase} Upstream: {cause_text}. Downstream: {effect_text}. Runtime: {runtime_text}."

    def _build_impact_summary_locked(self, cause_chain: list[str], effect_chain: list[str]) -> str:
        if effect_chain:
            visible = ", ".join(effect_chain[:3])
            suffix = "" if len(effect_chain) <= 3 else f" (+{len(effect_chain) - 3} more)"
            return f"Primary impact propagates downstream to {visible}{suffix}."
        if cause_chain:
            visible = ", ".join(cause_chain[:3])
            suffix = "" if len(cause_chain) <= 3 else f" (+{len(cause_chain) - 3} more)"
            return f"Behavior is mainly driven by upstream nodes {visible}{suffix}."
        return "No adjacent deterministic impact path found."

    def _compute_behavior_confidence_locked(
        self,
        row: RowModel,
        runtime: RuntimeState | None,
        cause_chain: list[str],
        effect_chain: list[str],
    ) -> float:
        base = max(0.0, min(1.0, float(row.confidence)))
        runtime_score = 0.0
        if runtime is not None:
            populated = sum(1 for value in [runtime.current_value, runtime.state, runtime.setpoint, runtime.mode] if value is not None)
            runtime_score = 0.05 * populated

        topology_score = min(0.2, 0.02 * (len(cause_chain) + len(effect_chain)))
        penalty = 0.08 if row.is_orphan else 0.0

        return round(max(0.0, min(1.0, base + runtime_score + topology_score - penalty)), 4)

    def _resolve_ranked_chains_locked(self, tag: str, max_depth: int) -> dict[str, Any]:
        resolver = WhyChainResolver()
        requested_tag = str(tag or "").strip()
        normalized_requested_tag = self.normalize_tag(requested_tag)
        node_roles = {
            row_tag: self._classify_why_role_locked(row)[0]
            for row_tag, row in self._rows_by_tag.items()
        }

        norm_to_canonical: dict[str, str] = {}
        for row_tag in self._rows_by_tag.keys():
            normalized = self.normalize_tag(row_tag)
            if normalized and normalized not in norm_to_canonical:
                norm_to_canonical[normalized] = row_tag

        def canonicalize_tag(raw: str) -> str:
            text = str(raw or "").strip()
            normalized = self.normalize_tag(text)
            if normalized and normalized in norm_to_canonical:
                return norm_to_canonical[normalized]
            return text

        selected_tag = canonicalize_tag(requested_tag)
        normalized_selected_tag = self.normalize_tag(selected_tag)
        selected_exists = selected_tag in self._rows_by_tag

        logger.info(
            "[WHY_CHAIN_DEBUG] start resolving selected_tag_api=%s selected_tag_engine=%s selected_tag_graph_builder=%s",
            requested_tag,
            selected_tag,
            selected_tag,
        )
        logger.info(
            "[WHY_CHAIN_DEBUG] selected_tag_normalization raw=%s normalized=%s canonical=%s canonical_normalized=%s exists_in_nodes=%s",
            requested_tag,
            normalized_requested_tag,
            selected_tag,
            normalized_selected_tag,
            selected_exists,
        )

        incoming_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        outgoing_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in self._edges:
            source_tag = canonicalize_tag(edge.source)
            target_tag = canonicalize_tag(edge.target)
            edge_payload = {
                "source": source_tag,
                "target": target_tag,
                "edge_type": edge.edge_type,
                "confidence": edge.confidence if edge.confidence is not None else 1.0,
                "source_type": edge.source_type,
            }
            outgoing_edges[source_tag].append(edge_payload)
            incoming_edges[target_tag].append(edge_payload)

        immediate_incoming_neighbors = sorted(
            {
                str(item.get("source", "")).strip()
                for item in (incoming_edges.get(selected_tag, []) or [])
                if str(item.get("source", "")).strip()
            }
        )
        immediate_outgoing_neighbors = sorted(
            {
                str(item.get("target", "")).strip()
                for item in (outgoing_edges.get(selected_tag, []) or [])
                if str(item.get("target", "")).strip()
            }
        )

        logger.info(
            "[WHY_CHAIN_DEBUG] totals nodes=%s edges=%s incoming_count=%s outgoing_count=%s",
            len(self._rows_by_tag),
            len(self._edges),
            len(incoming_edges.get(selected_tag, [])),
            len(outgoing_edges.get(selected_tag, [])),
        )
        logger.info("[WHY_CHAIN_DEBUG] immediate_incoming_neighbors=%s", immediate_incoming_neighbors)
        logger.info("[WHY_CHAIN_DEBUG] immediate_outgoing_neighbors=%s", immediate_outgoing_neighbors)

        upstream_candidate_paths = self._estimate_candidate_paths_locked(
            target_tag=selected_tag,
            direction="upstream",
            adjacency=incoming_edges,
            max_depth=max_depth,
            max_paths=8,
        )
        downstream_candidate_paths = self._estimate_candidate_paths_locked(
            target_tag=selected_tag,
            direction="downstream",
            adjacency=outgoing_edges,
            max_depth=max_depth,
            max_paths=8,
        )
        logger.info(
            "[WHY_CHAIN_DEBUG] resolver_called=%s upstream_candidate_paths=%s downstream_candidate_paths=%s",
            True,
            upstream_candidate_paths,
            downstream_candidate_paths,
        )

        chain_resolution = resolver.resolve_ranked_chains(
            target_tag=selected_tag,
            nodes=self._rows_by_tag,
            incoming_edges=incoming_edges,
            outgoing_edges=outgoing_edges,
            node_roles=node_roles,
            max_depth=max_depth,
            max_paths=8,
        )

        ranked_upstream = chain_resolution.get("ranked_upstream", []) or []
        ranked_downstream = chain_resolution.get("ranked_downstream", []) or []

        if not ranked_upstream and incoming_edges.get(selected_tag):
            ranked_upstream = self._fallback_ranked_chains_locked(
                target_tag=selected_tag,
                direction="upstream",
                adjacency=incoming_edges,
                max_depth=max_depth,
                max_paths=8,
            )
            chain_resolution["ranked_upstream"] = ranked_upstream

        if not ranked_downstream and outgoing_edges.get(selected_tag):
            ranked_downstream = self._fallback_ranked_chains_locked(
                target_tag=selected_tag,
                direction="downstream",
                adjacency=outgoing_edges,
                max_depth=max_depth,
                max_paths=8,
            )
            chain_resolution["ranked_downstream"] = ranked_downstream

        if not chain_resolution.get("merged_context"):
            up_tags = {
                node
                for chain in (chain_resolution.get("ranked_upstream", []) or [])
                for node in (chain.get("nodes", []) or [])
                if node and node != selected_tag
            }
            down_tags = {
                node
                for chain in (chain_resolution.get("ranked_downstream", []) or [])
                for node in (chain.get("nodes", []) or [])
                if node and node != selected_tag
            }
            chain_resolution["merged_context"] = {
                "parallel_upstream_tags": sorted(up_tags),
                "parallel_downstream_tags": sorted(down_tags),
                "parallel_context_tags": sorted(up_tags | down_tags),
            }

        upstream_paths = chain_resolution.get("ranked_upstream", []) or []
        downstream_paths = chain_resolution.get("ranked_downstream", []) or []
        zero_reason = ""
        if len(upstream_paths) == 0 and len(downstream_paths) == 0:
            if not selected_exists:
                zero_reason = "selected_tag_absent"
            elif len(incoming_edges.get(selected_tag, [])) == 0 and len(outgoing_edges.get(selected_tag, [])) == 0:
                zero_reason = "no_incoming_adjacency_and_no_outgoing_adjacency"
            elif upstream_candidate_paths == 0 and downstream_candidate_paths == 0:
                zero_reason = "all_paths_filtered_or_not_discovered"
            else:
                zero_reason = "resolver_returned_empty"

        chain_resolution["diagnostics"] = {
            "requested_tag": requested_tag,
            "normalized_requested_tag": normalized_requested_tag,
            "selected_tag": selected_tag,
            "normalized_selected_tag": normalized_selected_tag,
            "exists_in_nodes": selected_exists,
            "total_nodes": len(self._rows_by_tag),
            "total_edges": len(self._edges),
            "incoming_count": len(incoming_edges.get(selected_tag, [])),
            "outgoing_count": len(outgoing_edges.get(selected_tag, [])),
            "incoming_neighbors": immediate_incoming_neighbors,
            "outgoing_neighbors": immediate_outgoing_neighbors,
            "resolver_called": True,
            "upstream_candidate_paths": upstream_candidate_paths,
            "downstream_candidate_paths": downstream_candidate_paths,
            "ranked_upstream_returned": len(upstream_paths),
            "ranked_downstream_returned": len(downstream_paths),
            "zero_reason": zero_reason,
        }

        logger.info("[WHY_CHAIN_DEBUG] upstream_paths=%s", len(upstream_paths))
        logger.info("[WHY_CHAIN_DEBUG] downstream_paths=%s", len(downstream_paths))

        if upstream_paths:
            logger.info("[WHY_CHAIN_DEBUG] sample_upstream=%s", (upstream_paths[0] or {}))
        if downstream_paths:
            logger.info("[WHY_CHAIN_DEBUG] sample_downstream=%s", (downstream_paths[0] or {}))

        return chain_resolution

    def _estimate_candidate_paths_locked(
        self,
        *,
        target_tag: str,
        direction: str,
        adjacency: Mapping[str, list[dict[str, Any]]],
        max_depth: int,
        max_paths: int,
    ) -> int:
        queue: deque[tuple[str, set[str], int]] = deque([(target_tag, {target_tag}, 0)])
        count = 0
        hard_limit = max_paths * 20

        while queue and count < hard_limit:
            current, visited, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for raw in (adjacency.get(current, []) or []):
                neighbor = str(raw.get("source") if direction == "upstream" else raw.get("target") or "").strip()
                if not neighbor:
                    continue
                count += 1
                if count >= hard_limit:
                    break
                if neighbor in visited:
                    continue
                next_visited = set(visited)
                next_visited.add(neighbor)
                queue.append((neighbor, next_visited, depth + 1))

            if count >= hard_limit:
                break

        return count

    def _fallback_ranked_chains_locked(
        self,
        *,
        target_tag: str,
        direction: str,
        adjacency: Mapping[str, list[dict[str, Any]]],
        max_depth: int,
        max_paths: int,
    ) -> list[dict[str, Any]]:
        queue: deque[tuple[list[str], list[dict[str, Any]], int]] = deque([([target_tag], [], 0)])
        seen_paths: set[tuple[str, ...]] = set()
        results: list[dict[str, Any]] = []

        while queue and len(results) < max_paths:
            nodes, edges, depth = queue.popleft()
            current = nodes[-1]
            raw_edges = list(adjacency.get(current, []) or [])
            if not raw_edges:
                continue

            for raw in raw_edges:
                source = str(raw.get("source", "") or "").strip()
                target = str(raw.get("target", "") or "").strip()
                rel_type = str(raw.get("edge_type") or raw.get("rel_type") or "RELATED_TO").strip() or "RELATED_TO"
                source_type = str(raw.get("source_type") or "explicit").strip() or "explicit"
                try:
                    confidence = float(raw.get("confidence", 1.0))
                except (TypeError, ValueError):
                    confidence = 1.0
                confidence = max(0.0, min(1.0, confidence))

                neighbor = source if direction == "upstream" else target
                if not neighbor:
                    continue

                next_nodes = nodes + [neighbor]
                signature = tuple(next_nodes)
                if signature in seen_paths:
                    continue

                next_edges = edges + [
                    {
                        "source": source,
                        "target": target,
                        "rel_type": rel_type,
                        "confidence": confidence,
                        "source_type": source_type,
                    }
                ]

                weak_links: list[dict[str, Any]] = []
                if confidence < 0.8:
                    weak_links.append(
                        {
                            "index": len(next_edges) - 1,
                            "source": source,
                            "target": target,
                            "rel_type": rel_type,
                            "confidence": confidence,
                            "reasons": ["low_confidence"],
                        }
                    )

                cycle_detected = neighbor in nodes
                score = round(max(0.0, (0.78 * confidence) + 0.22 - (0.03 * (len(next_nodes) - 1))), 6)
                results.append(
                    {
                        "nodes": next_nodes,
                        "edges": next_edges,
                        "score": score,
                        "broken": cycle_detected,
                        "break_reason": "cycle_detected" if cycle_detected else "path_end",
                        "weak_links": weak_links,
                    }
                )
                seen_paths.add(signature)

                if len(results) >= max_paths:
                    break

                if depth + 1 < max_depth and not cycle_detected:
                    queue.append((next_nodes, next_edges, depth + 1))

            if len(results) >= max_paths:
                break

        return results

    def _build_why_trace_locked(
        self,
        tag: str,
        max_depth: int,
        chain_resolution: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []

        row = self._rows_by_tag.get(tag)
        if row is None:
            return steps

        runtime = self._runtime_by_tag.get(tag)
        steps.append(
            {
                "depth": 0,
                "direction": "self",
                "tag": tag,
                "edge_type": None,
                "runtime_state": runtime.as_dict() if runtime else None,
                "behavior_summary": row.behavior_summary,
            }
        )

        if chain_resolution:
            ranked_upstream = chain_resolution.get("ranked_upstream", []) or []
            ranked_downstream = chain_resolution.get("ranked_downstream", []) or []
            ordered_from_ranked = self._ranked_paths_to_steps_locked(tag, ranked_upstream, ranked_downstream, max_depth)
            if ordered_from_ranked:
                return ordered_from_ranked

        def traverse(direction: str) -> None:
            adjacency = self._inbound if direction == "upstream" else self._outbound
            queue: deque[tuple[str, int]] = deque([(tag, 0)])
            visited: set[str] = {tag}

            while queue:
                current, depth = queue.popleft()
                if depth >= max_depth:
                    continue

                for neighbor in sorted(adjacency.get(current, set())):
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

                    neighbor_row = self._rows_by_tag.get(neighbor)
                    neighbor_runtime = self._runtime_by_tag.get(neighbor)
                    steps.append(
                        {
                            "depth": depth + 1,
                            "direction": direction,
                            "tag": neighbor,
                            "edge_type": self._edge_type_pairs.get((neighbor, current))
                            if direction == "upstream"
                            else self._edge_type_pairs.get((current, neighbor)),
                            "runtime_state": neighbor_runtime.as_dict() if neighbor_runtime else None,
                            "behavior_summary": neighbor_row.behavior_summary if neighbor_row else "",
                        }
                    )

        traverse("upstream")
        traverse("downstream")

        steps.sort(key=lambda item: (item["depth"], item["direction"], item["tag"]))
        return steps

    def _ranked_paths_to_steps_locked(
        self,
        tag: str,
        ranked_upstream: list[dict[str, Any]],
        ranked_downstream: list[dict[str, Any]],
        max_depth: int,
    ) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        seen: set[tuple[str, str, int]] = set()

        root_runtime = self._runtime_by_tag.get(tag)
        root_row = self._rows_by_tag.get(tag)
        if root_row is None:
            return steps

        root_key = (tag, "self", 0)
        seen.add(root_key)
        steps.append(
            {
                "depth": 0,
                "direction": "self",
                "tag": tag,
                "edge_type": None,
                "runtime_state": root_runtime.as_dict() if root_runtime else None,
                "behavior_summary": root_row.behavior_summary,
            }
        )

        def append_from_ranked(chains: list[dict[str, Any]], direction: str) -> None:
            for chain in chains:
                nodes = [str(item).strip() for item in (chain.get("nodes", []) or []) if str(item).strip()]
                edges = chain.get("edges", []) or []
                if len(nodes) <= 1:
                    continue

                traversal = list(reversed(nodes[:-1])) if direction == "upstream" else nodes[1:]
                max_len = min(max_depth, len(traversal))
                for index in range(max_len):
                    node_tag = traversal[index]
                    depth = index + 1
                    key = (node_tag, direction, depth)
                    if key in seen:
                        continue

                    neighbor_row = self._rows_by_tag.get(node_tag)
                    neighbor_runtime = self._runtime_by_tag.get(node_tag)
                    edge_type: str | None = None
                    if direction == "upstream":
                        edge_index = len(edges) - depth
                        if 0 <= edge_index < len(edges):
                            edge_type = str((edges[edge_index] or {}).get("rel_type") or "") or None
                    else:
                        edge_index = depth - 1
                        if 0 <= edge_index < len(edges):
                            edge_type = str((edges[edge_index] or {}).get("rel_type") or "") or None

                    steps.append(
                        {
                            "depth": depth,
                            "direction": direction,
                            "tag": node_tag,
                            "edge_type": edge_type,
                            "runtime_state": neighbor_runtime.as_dict() if neighbor_runtime else None,
                            "behavior_summary": neighbor_row.behavior_summary if neighbor_row else "",
                        }
                    )
                    seen.add(key)

        append_from_ranked(ranked_upstream, "upstream")
        append_from_ranked(ranked_downstream, "downstream")
        steps.sort(key=lambda item: (item["depth"], item["direction"], item["tag"]))
        return steps


deterministic_behavior_service = DeterministicBehaviorService()
