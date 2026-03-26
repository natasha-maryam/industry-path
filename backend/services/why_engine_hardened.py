from __future__ import annotations

import asyncio
from copy import deepcopy
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Mapping

from services.why_chain_resolver import WhyChainResolver
from services.why_graph_builder import WhyGraphBuilder, WhyEdge
from services.why_narrative_engine import WhyNarrativeEngine


class WhyEngineHardened:
    def __init__(self, cache_size: int = 256) -> None:
        self._cache_size = max(8, int(cache_size))
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_order: list[str] = []
        self._lock = RLock()
        self._graph_builder = WhyGraphBuilder()
        self._chain_resolver = WhyChainResolver()
        self._narrative_engine = WhyNarrativeEngine()

    async def generate_async(
        self,
        tag: str,
        rows: list[Mapping[str, Any]],
        edges: list[Mapping[str, Any]] | None = None,
        version: str = "v1",
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self.generate, tag, rows, edges, version)

    def generate(
        self,
        tag: str,
        rows: list[Mapping[str, Any]],
        edges: list[Mapping[str, Any]] | None = None,
        version: str = "v1",
    ) -> dict[str, Any]:
        safe_rows = [dict(row) for row in (rows or []) if isinstance(row, Mapping)]
        safe_edges = [dict(edge) for edge in (edges or []) if isinstance(edge, Mapping)]

        cache_key = self._cache_key(tag=tag, rows=safe_rows, edges=safe_edges, version=version)
        cached = self._cache_get(cache_key)
        if cached is not None:
            payload = deepcopy(cached)
            payload.setdefault("debug", {})
            payload["debug"]["cache_hit"] = True
            return payload

        selected_tag_raw = str(tag or "").strip()
        normalized_selected = self._normalize_tag(selected_tag_raw)

        row_by_tag: dict[str, dict[str, Any]] = {}
        normalized_to_tag: dict[str, str] = {}
        for row in safe_rows:
            row_tag = str(row.get("tag", "") or "").strip()
            if not row_tag:
                continue
            row_by_tag[row_tag] = row
            normalized = self._normalize_tag(row_tag)
            if normalized and normalized not in normalized_to_tag:
                normalized_to_tag[normalized] = row_tag

        selected_tag = normalized_to_tag.get(normalized_selected, selected_tag_raw)
        selected_row = row_by_tag.get(selected_tag)

        if not safe_rows:
            result = self._empty_result(
                tag=selected_tag_raw,
                reason="empty_rows",
                cache_key=cache_key,
            )
            self._cache_set(cache_key, result)
            return deepcopy(result)

        graph = self._graph_builder.build_graph(safe_rows, explicit_edges=safe_edges)

        incoming_edges: dict[str, list[dict[str, Any]]] = {}
        outgoing_edges: dict[str, list[dict[str, Any]]] = {}
        for key, items in graph.incoming.items():
            incoming_edges[key] = [self._edge_to_payload(item) for item in items]
        for key, items in graph.outgoing.items():
            outgoing_edges[key] = [self._edge_to_payload(item) for item in items]

        node_roles: dict[str, str] = {
            row_tag: self._classify_role(row_payload)
            for row_tag, row_payload in row_by_tag.items()
        }

        if selected_row is None:
            reason = "selected_tag_absent"
            if normalized_selected and normalized_selected in normalized_to_tag:
                reason = "normalized_key_mismatch"
            result = self._empty_result(
                tag=selected_tag_raw,
                reason=reason,
                cache_key=cache_key,
            )
            result["debug"]["rows_count"] = len(row_by_tag)
            result["debug"]["edges_count"] = len(graph.edges)
            self._cache_set(cache_key, result)
            return deepcopy(result)

        chains = self._chain_resolver.resolve_ranked_chains(
            target_tag=selected_tag,
            nodes=row_by_tag,
            incoming_edges=incoming_edges,
            outgoing_edges=outgoing_edges,
            node_roles=node_roles,
            max_depth=4,
            max_paths=8,
        )

        structure = self._to_structure(chains)
        explanation = self._narrative_engine.build(
            target_tag=selected_tag,
            target_role=node_roles.get(selected_tag, "unknown"),
            target_type=str(selected_row.get("type") or "") or None,
            target_subtype=str(selected_row.get("subtype") or "") or None,
            behavior_summary=str(selected_row.get("behavior_summary") or "") or None,
            ranked_upstream=structure.get("ranked_upstream", []) or [],
            ranked_downstream=structure.get("ranked_downstream", []) or [],
            runtime_state={
                "current_value": selected_row.get("current_value"),
                "state": selected_row.get("state"),
                "setpoint": selected_row.get("setpoint"),
                "mode": selected_row.get("mode"),
                "unit": selected_row.get("unit"),
            },
            diagnostics_reason=str((structure.get("diagnostics") or {}).get("reason") or ""),
        )

        warnings = explanation.get("warnings")
        if not isinstance(warnings, list):
            explanation["warnings"] = []

        result = {
            "tag": selected_tag,
            "structure": structure,
            "explanation": explanation,
            "debug": {
                "cache_hit": False,
                "cache_key": cache_key,
                "rows_count": len(row_by_tag),
                "edges_count": len(graph.edges),
            },
        }

        self._cache_set(cache_key, result)
        return deepcopy(result)

    def _cache_key(
        self,
        *,
        tag: str,
        rows: list[Mapping[str, Any]],
        edges: list[Mapping[str, Any]],
        version: str,
    ) -> str:
        normalized_tag = self._normalize_tag(tag)

        row_signature = [
            {
                "tag": str(row.get("tag") or "").strip(),
                "type": str(row.get("type") or "").strip(),
                "subtype": str(row.get("subtype") or "").strip(),
                "upstream": sorted(str(item).strip() for item in (row.get("upstream") or []) if str(item).strip()),
                "downstream": sorted(str(item).strip() for item in (row.get("downstream") or []) if str(item).strip()),
                "controls": sorted(str(item).strip() for item in (row.get("controls") or []) if str(item).strip()),
                "controlled_by": sorted(str(item).strip() for item in (row.get("controlled_by") or []) if str(item).strip()),
                "signal_inputs": sorted(str(item).strip() for item in (row.get("signal_inputs") or []) if str(item).strip()),
                "signal_outputs": sorted(str(item).strip() for item in (row.get("signal_outputs") or []) if str(item).strip()),
                "behavior_summary": str(row.get("behavior_summary") or "").strip(),
                "current_value": str(row.get("current_value") or "").strip(),
                "state": str(row.get("state") or "").strip(),
                "setpoint": str(row.get("setpoint") or "").strip(),
                "mode": str(row.get("mode") or "").strip(),
            }
            for row in rows
        ]
        row_signature.sort(key=lambda item: item.get("tag") or "")
        rows_hash = sha256(json.dumps(row_signature, sort_keys=True).encode("utf-8")).hexdigest()

        edge_signature = [
            {
                "source": str(edge.get("source") or "").strip(),
                "target": str(edge.get("target") or "").strip(),
                "edge_type": str(edge.get("edge_type") or edge.get("type") or "").strip(),
                "confidence": edge.get("confidence"),
                "source_type": str(edge.get("source_type") or "").strip(),
                "inferred": bool(edge.get("inferred", False)),
            }
            for edge in edges
        ]
        edge_signature.sort(key=lambda item: (item.get("source") or "", item.get("target") or "", item.get("edge_type") or ""))
        edges_hash = sha256(json.dumps(edge_signature, sort_keys=True).encode("utf-8")).hexdigest()

        return f"{version}:{normalized_tag}:{rows_hash}:{edges_hash}"

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            item = self._cache.get(key)
            return deepcopy(item) if item is not None else None

    def _cache_set(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._cache[key] = deepcopy(value)
            if key in self._cache_order:
                self._cache_order.remove(key)
            self._cache_order.append(key)

            while len(self._cache_order) > self._cache_size:
                victim = self._cache_order.pop(0)
                self._cache.pop(victim, None)

    def _to_structure(self, chains: Mapping[str, Any]) -> dict[str, Any]:
        ranked_upstream = self._normalize_ranked(chains.get("ranked_upstream", []) or [])
        ranked_downstream = self._normalize_ranked(chains.get("ranked_downstream", []) or [])
        merged_context = dict(chains.get("merged_context", {}) or {})

        diagnostics_reason = ""
        if not ranked_upstream and not ranked_downstream:
            diagnostics_reason = "no_ranked_paths"

        return {
            "chains": {
                "ranked_upstream": ranked_upstream,
                "ranked_downstream": ranked_downstream,
                "merged_context": merged_context,
            },
            "ranked_upstream": ranked_upstream,
            "ranked_downstream": ranked_downstream,
            "merged_context": {
                "parallel_upstream": [
                    str(item).strip()
                    for item in (merged_context.get("parallel_upstream_tags", []) or [])
                    if str(item).strip()
                ],
                "parallel_downstream": [
                    str(item).strip()
                    for item in (merged_context.get("parallel_downstream_tags", []) or [])
                    if str(item).strip()
                ],
            },
            "diagnostics": {
                "reason": diagnostics_reason,
                "ranked_upstream_count": len(ranked_upstream),
                "ranked_downstream_count": len(ranked_downstream),
            },
        }

    def _normalize_ranked(self, chains: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in chains:
            tags = [str(tag).strip() for tag in (item.get("nodes", []) or []) if str(tag).strip()]
            weak_links = list(item.get("weak_links", []) or [])
            broken = bool(item.get("broken", False))

            score_raw = item.get("score")
            try:
                score = float(score_raw)
            except (TypeError, ValueError):
                score = 0.0

            break_reason_raw = str(item.get("break_reason", "")).strip()

            normalized.append(
                {
                    "tags": tags,
                    "score": round(score, 6),
                    "depth": max(0, len(tags) - 1),
                    "weak_links": weak_links,
                    "broken": broken,
                    "break_reason": break_reason_raw if broken and break_reason_raw else None,
                }
            )

        return normalized

    def _empty_result(self, *, tag: str, reason: str, cache_key: str) -> dict[str, Any]:
        explanation = self._narrative_engine.build(
            target_tag=tag,
            target_role="unknown",
            target_type=None,
            target_subtype=None,
            behavior_summary=None,
            ranked_upstream=[],
            ranked_downstream=[],
            runtime_state=None,
            diagnostics_reason=reason,
        )
        warnings = explanation.get("warnings")
        if not isinstance(warnings, list):
            explanation["warnings"] = []

        return {
            "tag": tag,
            "structure": {
                "chains": {
                    "ranked_upstream": [],
                    "ranked_downstream": [],
                    "merged_context": {
                        "parallel_upstream_tags": [],
                        "parallel_downstream_tags": [],
                        "parallel_context_tags": [],
                    },
                },
                "ranked_upstream": [],
                "ranked_downstream": [],
                "merged_context": {
                    "parallel_upstream": [],
                    "parallel_downstream": [],
                },
                "diagnostics": {
                    "reason": reason,
                    "ranked_upstream_count": 0,
                    "ranked_downstream_count": 0,
                },
            },
            "explanation": explanation,
            "debug": {
                "cache_hit": False,
                "cache_key": cache_key,
                "rows_count": 0,
                "edges_count": 0,
            },
        }

    @staticmethod
    def _edge_to_payload(edge: WhyEdge) -> dict[str, Any]:
        return {
            "source": edge.source,
            "target": edge.target,
            "edge_type": edge.rel_type,
            "confidence": edge.confidence,
            "source_type": edge.source_type,
            "inferred": edge.inferred,
        }

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        raw = str(tag or "").strip().upper()
        if not raw:
            return ""
        return "".join(ch for ch in raw if ch.isalnum())

    @staticmethod
    def _classify_role(row: Mapping[str, Any]) -> str:
        tag_text = str(row.get("tag") or "").strip().upper()
        type_text = str(row.get("type") or "").strip().lower()
        subtype_text = str(row.get("subtype") or "").strip().lower()

        for prefix in ("AIT", "FIT", "LIT", "PIT", "DPIT"):
            if tag_text.startswith(prefix):
                return "sensor"
        if any(token in subtype_text for token in ("sensor", "transmitter", "analyzer")):
            return "sensor"

        for prefix in ("FCV", "VAL", "PMP", "BL", "MOTOR"):
            if tag_text.startswith(prefix):
                return "actuator"
        if any(token in subtype_text for token in ("valve", "pump", "actuator", "blower")):
            return "actuator"

        if any(token in tag_text for token in ("CTRL", "LOOP", "PID")):
            return "controller"

        if "process" in type_text or any(token in tag_text for token in ("BAS", "TANK", "AREA")):
            return "process_unit"

        return "unknown"
