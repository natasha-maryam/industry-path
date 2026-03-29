from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass
from statistics import mean

from db.postgres import postgres_client
from models.document_pipeline import BehavioralChainRecord
from models.engineering_table import (
    EngineeringLinkReference,
    EngineeringTableRequest,
    EngineeringTableResponse,
    EngineeringTableRow,
    EngineeringTableSummaryStats,
    EngineeringTableWarning,
    EngineeringTraceabilityItem,
)
from models.graph import GraphEdge, GraphNode
from services.graph_service import graph_service
from services.project_service import project_service
from services.signal_classification import process_role_from_node


@dataclass(frozen=True)
class IngestedProjectData:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    documents: list[dict]
    metadata_rows: list[dict]


@dataclass(frozen=True)
class _CandidateLink:
    tag: str
    provenance: str
    inferred: bool
    priority: int
    rank: tuple[object, ...]


class EngineeringTableParser:
    def build(self, payload: EngineeringTableRequest) -> EngineeringTableResponse:
        project_service.ensure_project(payload.project_id)

        ingested = self._document_ingestion(payload)
        normalized_nodes = self._text_normalization(ingested.nodes)
        extracted_entities = self._entity_extraction(normalized_nodes)
        canonical_entities, duplicate_warnings = self._tag_normalization(extracted_entities)

        context = self._context_mapping(
            entities=canonical_entities,
            documents=ingested.documents,
            metadata_rows=ingested.metadata_rows,
        )
        behavioral_chains = self._behavioral_chain_extraction(ingested.metadata_rows)
        relationships = self._relationship_extraction(canonical_entities, ingested.edges)
        loops = self._control_loop_detection(canonical_entities, relationships, behavioral_chains=behavioral_chains)
        updown = self._upstream_downstream_calculation(
            entities=canonical_entities,
            relationships=relationships,
            loops=loops,
            behavioral_chains=behavioral_chains,
            metadata_rows=ingested.metadata_rows,
            max_depth=max(2, payload.max_flow_depth),
        )
        metadata = self._engineering_metadata_extraction(canonical_entities)
        traceability = self._traceability_mapping(canonical_entities, context, relationships)
        derived = self._derived_field_generation(canonical_entities, relationships, loops, updown)

        rows = self._row_building(
            entities=canonical_entities,
            context=context,
            relationships=relationships,
            loops=loops,
            updown=updown,
            metadata=metadata,
            traceability=traceability,
            derived=derived,
            include_inferred=payload.include_inferred,
        )

        self._confidence_scoring(rows)
        self._annotate_row_warnings(rows)
        warnings = [*duplicate_warnings, *self._quality_warnings(rows, relationships)]
        summary = self._summary(rows)
        return EngineeringTableResponse(
            project_id=payload.project_id,
            rows=rows,
            warnings=warnings,
            summary=summary,
        )

    def _document_ingestion(self, payload: EngineeringTableRequest) -> IngestedProjectData:
        graph = graph_service.get_graph(payload.project_id)

        if payload.file_ids:
            placeholders = ",".join(["%s"] * len(payload.file_ids))
            docs = postgres_client.fetch_all(
                f"""
                SELECT id::text AS id, project_id::text AS project_id, original_name, document_type, uploaded_at
                FROM project_files
                WHERE project_id = %s AND id::text IN ({placeholders})
                ORDER BY uploaded_at DESC NULLS LAST
                """,
                (payload.project_id, *payload.file_ids),
            )
        else:
            docs = postgres_client.fetch_all(
                """
                SELECT id::text AS id, project_id::text AS project_id, original_name, document_type, uploaded_at
                FROM project_files
                WHERE project_id = %s
                ORDER BY uploaded_at DESC NULLS LAST
                """,
                (payload.project_id,),
            )

        metadata_rows = postgres_client.fetch_all(
            """
            SELECT id::text AS id,
                   category,
                   tag,
                   payload,
                   created_at,
                   parse_batch_id::text AS parse_batch_id,
                   source_file_id::text AS source_file_id
            FROM extracted_metadata
            WHERE project_id = %s
            ORDER BY created_at DESC NULLS LAST
            LIMIT 2000
            """,
            (payload.project_id,),
        )

        return IngestedProjectData(nodes=graph.nodes, edges=graph.edges, documents=docs, metadata_rows=metadata_rows)

    def _text_normalization(self, nodes: list[GraphNode]) -> list[GraphNode]:
        normalized: list[GraphNode] = []
        for node in nodes:
            cleaned_id = self._normalize_token(node.id)
            cleaned_label = self._normalize_sentence(node.label)
            metadata = dict(node.metadata) if isinstance(node.metadata, dict) else {}
            if cleaned_id != node.id:
                metadata["normalized_tag"] = cleaned_id
            normalized.append(
                node.model_copy(
                    update={
                        "id": cleaned_id,
                        "label": cleaned_label,
                        "metadata": metadata,
                    }
                )
            )
        return normalized

    def _entity_extraction(self, nodes: list[GraphNode]) -> list[dict]:
        entities: list[dict] = []
        for node in nodes:
            role = process_role_from_node(node.node_type)
            metadata = dict(node.metadata) if isinstance(node.metadata, dict) else {}
            entities.append(
                {
                    "id": node.id,
                    "tag": node.id,
                    "type": node.normalized_type or node.node_type,
                    "subtype": node.node_type,
                    "description": node.description or node.label,
                    "system": node.process_unit,
                    "equipment": node.equipment_type or node.normalized_type or node.node_type,
                    "process_role": role,
                    "status": node.status,
                    "mode": node.mode,
                    "power": node.power_rating,
                    "metadata": metadata,
                    "is_synthetic": bool(node.is_synthetic),
                    "source_documents": [str(item) for item in (node.source_documents or []) if item],
                    "source_references": [str(item) for item in (node.source_references or []) if item],
                    "node_confidence": float(node.confidence or 0.6),
                }
            )
        return entities

    def _tag_normalization(self, entities: list[dict]) -> tuple[list[dict], list[EngineeringTableWarning]]:
        by_tag: dict[str, dict] = {}
        duplicates: dict[str, list[dict]] = defaultdict(list)
        warnings: list[EngineeringTableWarning] = []

        for entity in entities:
            key = self._normalize_token(entity["tag"])
            previous = by_tag.get(key)
            if previous is None:
                by_tag[key] = entity
                continue
            duplicates[key].append(entity)
            if entity["node_confidence"] > previous["node_confidence"]:
                by_tag[key] = entity

        for tag, items in duplicates.items():
            warnings.append(
                EngineeringTableWarning(
                    code="duplicate_tag",
                    severity="warning",
                    message=f"Duplicate tag candidates resolved deterministically for {tag}.",
                    affected_tags=[tag, *[str(item.get("tag", "")) for item in items]],
                )
            )

        return list(by_tag.values()), warnings

    def _context_mapping(self, entities: list[dict], documents: list[dict], metadata_rows: list[dict]) -> dict[str, dict]:
        entity_by_tag = {self._normalize_token(item["tag"]): item for item in entities}
        context: dict[str, dict] = {
            self._normalize_token(item["tag"]): {
                "document_source": sorted(set(str(value) for value in item.get("source_documents", []) if value)),
                "line_reference": [],
                "metadata_matches": [],
            }
            for item in entities
        }

        default_doc_names = [str(item.get("original_name", "")) for item in documents if item.get("original_name")]

        for row in metadata_rows:
            row_tag = self._normalize_token(str(row.get("tag") or ""))
            if row_tag not in entity_by_tag:
                continue
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            category = str(row.get("category") or "metadata")
            source_file_id = row.get("source_file_id")
            line_hint = payload.get("line") or payload.get("line_reference") or payload.get("page")
            line_reference = f"{category}:{line_hint}" if line_hint else category
            context[row_tag]["line_reference"].append(str(line_reference))
            context[row_tag]["metadata_matches"].append(payload)

            source_doc = next((d for d in documents if d.get("id") == source_file_id), None)
            if source_doc and source_doc.get("original_name"):
                context[row_tag]["document_source"].append(str(source_doc["original_name"]))

        for item in context.values():
            if not item["document_source"] and default_doc_names:
                item["document_source"] = sorted(set(default_doc_names[:2]))
            else:
                item["document_source"] = sorted(set(item["document_source"]))
            item["line_reference"] = sorted(set(item["line_reference"]))

        return context

    def _relationship_extraction(self, entities: list[dict], edges: list[GraphEdge]) -> dict[str, dict[str, set[str]]]:
        available = {self._normalize_token(item["tag"]) for item in entities}
        relations: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

        for edge in edges:
            source = self._normalize_token(edge.source)
            target = self._normalize_token(edge.target)
            if source not in available or target not in available or source == target:
                continue

            edge_type = edge.edge_type.upper()
            relations[source]["connections"].add(target)
            relations[target]["connections"].add(source)

            if edge_type in {"MEASURES", "MONITORS"}:
                relations[source]["measures"].add(target)
                relations[target]["signal_inputs"].add(source)
            if edge_type in {"CONTROLS", "SIGNAL_TO"}:
                relations[source]["controls"].add(target)
                relations[target]["controlled_by"].add(source)
                relations[source]["signal_outputs"].add(target)
                relations[target]["signal_inputs"].add(source)
            if edge_type in {"PROCESS_FLOW", "FEEDS", "DISCHARGES_TO"}:
                relations[source]["downstream"].add(target)
                relations[target]["upstream"].add(source)

        return relations

    def _control_loop_detection(
        self,
        entities: list[dict],
        relationships: dict[str, dict[str, set[str]]],
        behavioral_chains: list[BehavioralChainRecord] | None = None,
    ) -> dict[str, list[str]]:
        by_role: dict[str, list[str]] = defaultdict(list)
        for entity in entities:
            role = str(entity.get("process_role") or "unknown")
            by_role[role].append(self._normalize_token(entity["tag"]))

        loops_by_tag: dict[str, list[str]] = defaultdict(list)
        for chain in behavioral_chains or []:
            chain_path = [self._normalize_token(item) for item in (chain.chain or [chain.sensor, chain.actuator, chain.process]) if item]
            if len(chain_path) != 3:
                continue
            chain_value = "->".join(chain_path)
            for tag in {chain.sensor, chain.actuator, chain.process}:
                loops_by_tag[self._normalize_token(tag)].append(chain_value)

        processes = by_role.get("process", [])

        for process_tag in processes:
            sensors = [tag for tag in by_role.get("sensor", []) if process_tag in relationships.get(tag, {}).get("measures", set())]
            actuators = [
                tag for tag in by_role.get("actuator", []) if process_tag in relationships.get(tag, {}).get("controls", set())
            ]
            for sensor in sensors:
                for actuator in actuators:
                    chain = f"{sensor}->{actuator}->{process_tag}"
                    loops_by_tag[sensor].append(chain)
                    loops_by_tag[process_tag].append(chain)
                    loops_by_tag[actuator].append(chain)

        return {tag: sorted(set(chains)) for tag, chains in loops_by_tag.items()}

    def _upstream_downstream_calculation(
        self,
        *,
        entities: list[dict],
        relationships: dict[str, dict[str, set[str]]],
        loops: dict[str, list[str]],
        behavioral_chains: list[BehavioralChainRecord] | None = None,
        metadata_rows: list[dict],
        max_depth: int,
    ) -> dict[str, dict[str, object]]:
        entity_map = {self._normalize_token(item["tag"]): item for item in entities}
        context_neighbors = self._context_neighbors(metadata_rows)
        result: dict[str, dict[str, object]] = {}

        for tag in sorted(entity_map):
            explicit_upstream = self._walk_graph(relationships, start=tag, key="upstream", max_depth=max_depth)
            explicit_downstream = self._walk_graph(relationships, start=tag, key="downstream", max_depth=max_depth)

            upstream_links = [EngineeringLinkReference(tag=item, provenance="explicit", inferred=False) for item in explicit_upstream]
            downstream_links = [EngineeringLinkReference(tag=item, provenance="explicit", inferred=False) for item in explicit_downstream]

            if not upstream_links:
                inferred = self._infer_directional_links(
                    tag=tag,
                    direction="upstream",
                    entity_map=entity_map,
                    relationships=relationships,
                    loops=loops,
                    behavioral_chains=behavioral_chains or [],
                    context_neighbors=context_neighbors,
                )
                upstream_links = [EngineeringLinkReference(tag=item.tag, provenance=item.provenance, inferred=item.inferred) for item in inferred]

            if not downstream_links:
                inferred = self._infer_directional_links(
                    tag=tag,
                    direction="downstream",
                    entity_map=entity_map,
                    relationships=relationships,
                    loops=loops,
                    behavioral_chains=behavioral_chains or [],
                    context_neighbors=context_neighbors,
                )
                downstream_links = [EngineeringLinkReference(tag=item.tag, provenance=item.provenance, inferred=item.inferred) for item in inferred]

            if not upstream_links:
                upstream_links = [EngineeringLinkReference(tag=self._sentinel_tag(entity_map[tag], "upstream"), provenance="sentinel_fallback", inferred=True)]
            if not downstream_links:
                downstream_links = [EngineeringLinkReference(tag=self._sentinel_tag(entity_map[tag], "downstream"), provenance="sentinel_fallback", inferred=True)]

            upstream = [item.tag for item in upstream_links]
            downstream = [item.tag for item in downstream_links]
            result[tag] = {
                "upstream": upstream,
                "downstream": downstream,
                "upstream_links": upstream_links,
                "downstream_links": downstream_links,
                "has_inferred_upstream": any(item.inferred for item in upstream_links),
                "has_inferred_downstream": any(item.inferred for item in downstream_links),
                "flow_chain": [*upstream, tag, *downstream],
            }

        return result

    def _infer_directional_links(
        self,
        *,
        tag: str,
        direction: str,
        entity_map: dict[str, dict],
        relationships: dict[str, dict[str, set[str]]],
        loops: dict[str, list[str]],
        behavioral_chains: list[BehavioralChainRecord],
        context_neighbors: dict[str, dict[str, list[str]]],
    ) -> list[_CandidateLink]:
        topology_candidates = self._topology_candidates(tag=tag, direction=direction, entity_map=entity_map, relationships=relationships)
        if topology_candidates:
            return topology_candidates

        behavioral_candidates = self._behavioral_chain_candidates(tag=tag, direction=direction, behavioral_chains=behavioral_chains, loops=loops)
        if behavioral_candidates:
            return behavioral_candidates

        context_candidates = self._context_candidates(tag=tag, direction=direction, context_neighbors=context_neighbors)
        if context_candidates:
            return context_candidates

        return []

    def _topology_candidates(
        self,
        *,
        tag: str,
        direction: str,
        entity_map: dict[str, dict],
        relationships: dict[str, dict[str, set[str]]],
    ) -> list[_CandidateLink]:
        entity = entity_map.get(tag, {})
        role = str(entity.get("process_role") or "unknown")
        system = self._normalize_token(str(entity.get("system") or ""))
        rel = relationships.get(tag, {})
        candidate_tags: set[str] = set()
        if direction == "upstream":
            candidate_tags.update(rel.get("controlled_by", set()))
            candidate_tags.update(rel.get("signal_inputs", set()))
            candidate_tags.update(rel.get("connections", set()))
        else:
            candidate_tags.update(rel.get("controls", set()))
            candidate_tags.update(rel.get("signal_outputs", set()))
            candidate_tags.update(rel.get("measures", set()))
            candidate_tags.update(rel.get("connections", set()))

        scored: list[_CandidateLink] = []
        for candidate in sorted(candidate_tags):
            if candidate == tag or candidate not in entity_map:
                continue
            candidate_entity = entity_map[candidate]
            candidate_system = self._normalize_token(str(candidate_entity.get("system") or ""))
            candidate_role = str(candidate_entity.get("process_role") or "unknown")
            same_system = candidate_system == system and bool(system)
            compatibility = self._directional_role_rank(role, candidate_role, direction)
            rank = (
                0 if same_system else 1,
                compatibility,
                0 if candidate in rel.get("connections", set()) else 1,
                candidate,
            )
            scored.append(_CandidateLink(tag=candidate, provenance="inferred_from_topology", inferred=True, priority=1, rank=rank))

        return self._select_best_candidates(scored)

    def _behavioral_chain_candidates(
        self,
        *,
        tag: str,
        direction: str,
        behavioral_chains: list[BehavioralChainRecord],
        loops: dict[str, list[str]],
    ) -> list[_CandidateLink]:
        candidates: list[_CandidateLink] = []
        normalized_tag = self._normalize_token(tag)
        for chain in behavioral_chains:
            chain_path = [self._normalize_token(item) for item in (chain.chain or [chain.sensor, chain.actuator, chain.process]) if item]
            if len(chain_path) != 3:
                continue
            sensor, actuator, process = chain_path
            candidate = None
            if normalized_tag == sensor:
                candidate = process if direction == "upstream" else actuator
            elif normalized_tag == actuator:
                candidate = sensor if direction == "upstream" else process
            elif normalized_tag == process:
                candidate = actuator if direction == "upstream" else sensor
            if candidate and candidate != normalized_tag:
                candidates.append(
                    _CandidateLink(
                        tag=candidate,
                        provenance="inferred_from_behavioral_chain",
                        inferred=True,
                        priority=2,
                        rank=(0, -int(chain.confidence * 1000), tuple(chain_path), candidate),
                    )
                )

        if candidates:
            return self._select_best_candidates(candidates)

        for chain in sorted(loops.get(tag, [])):
            parts = [segment.strip() for segment in chain.split("->") if segment.strip()]
            if len(parts) != 3:
                continue
            sensor, actuator, process = parts
            candidate = None
            if tag == sensor:
                candidate = process if direction == "upstream" else actuator
            elif tag == actuator:
                candidate = sensor if direction == "upstream" else process
            elif tag == process:
                candidate = actuator if direction == "upstream" else sensor
            if candidate and candidate != tag:
                candidates.append(
                    _CandidateLink(
                        tag=candidate,
                        provenance="inferred_from_behavioral_chain",
                        inferred=True,
                        priority=2,
                        rank=(chain, candidate),
                    )
                )
        return self._select_best_candidates(candidates)

    def _behavioral_chain_extraction(self, metadata_rows: list[dict]) -> list[BehavioralChainRecord]:
        chains_by_id: dict[str, BehavioralChainRecord] = {}
        for row in metadata_rows:
            if str(row.get("category") or "") != "behavioral_chain":
                continue
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            if not payload:
                continue
            try:
                chain = BehavioralChainRecord.model_validate(payload)
            except Exception:
                continue
            normalized_chain = chain.model_copy(
                update={
                    "sensor": self._normalize_token(chain.sensor),
                    "actuator": self._normalize_token(chain.actuator),
                    "process": self._normalize_token(chain.process),
                    "chain": [self._normalize_token(item) for item in (chain.chain or [chain.sensor, chain.actuator, chain.process]) if item],
                }
            )
            existing = chains_by_id.get(normalized_chain.chain_id)
            if existing is None or normalized_chain.confidence >= existing.confidence:
                chains_by_id[normalized_chain.chain_id] = normalized_chain
        return sorted(chains_by_id.values(), key=lambda item: (item.process, item.sensor, item.actuator))

    def _context_candidates(self, *, tag: str, direction: str, context_neighbors: dict[str, dict[str, list[str]]]) -> list[_CandidateLink]:
        candidates: list[_CandidateLink] = []
        for index, candidate in enumerate(context_neighbors.get(tag, {}).get(direction, [])):
            if candidate == tag:
                continue
            candidates.append(
                _CandidateLink(
                    tag=candidate,
                    provenance="inferred_from_context",
                    inferred=True,
                    priority=3,
                    rank=(index, candidate),
                )
            )
        return self._select_best_candidates(candidates)

    def _context_neighbors(self, metadata_rows: list[dict]) -> dict[str, dict[str, list[str]]]:
        context: dict[str, dict[str, list[tuple[tuple[object, ...], str]]]] = defaultdict(lambda: {"upstream": [], "downstream": []})
        for row in metadata_rows:
            if str(row.get("category") or "") != "extracted_relationship":
                continue
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            source = self._normalize_token(str(payload.get("source_tag") or ""))
            target = self._normalize_token(str(payload.get("target_tag") or ""))
            if not source or not target or source == target:
                continue
            page = payload.get("source_page") or 0
            section_reference = str(payload.get("source_section_reference") or "")
            relationship_type = str(payload.get("relationship_type") or "")
            rank = (int(page) if isinstance(page, int) or str(page).isdigit() else 0, section_reference, relationship_type, source, target)
            context[source]["downstream"].append((rank, target))
            context[target]["upstream"].append((rank, source))

        normalized: dict[str, dict[str, list[str]]] = {}
        for tag, directions in context.items():
            normalized[tag] = {}
            for direction, values in directions.items():
                ordered = sorted(values, key=lambda item: item[0])
                deduped: list[str] = []
                for _, candidate in ordered:
                    if candidate not in deduped:
                        deduped.append(candidate)
                normalized[tag][direction] = deduped
        return normalized

    @staticmethod
    def _directional_role_rank(role: str, candidate_role: str, direction: str) -> int:
        priority_map = {
            ("sensor", "upstream"): {"process": 0, "actuator": 1, "sensor": 2, "unknown": 3},
            ("sensor", "downstream"): {"actuator": 0, "process": 1, "sensor": 2, "unknown": 3},
            ("actuator", "upstream"): {"sensor": 0, "process": 1, "actuator": 2, "unknown": 3},
            ("actuator", "downstream"): {"process": 0, "actuator": 1, "sensor": 2, "unknown": 3},
            ("process", "upstream"): {"actuator": 0, "sensor": 1, "process": 2, "unknown": 3},
            ("process", "downstream"): {"actuator": 0, "sensor": 1, "process": 2, "unknown": 3},
        }
        return priority_map.get((role, direction), {}).get(candidate_role, 4)

    @staticmethod
    def _select_best_candidates(candidates: list[_CandidateLink]) -> list[_CandidateLink]:
        if not candidates:
            return []
        unique: dict[str, _CandidateLink] = {}
        for item in sorted(candidates, key=lambda candidate: (candidate.priority, candidate.rank)):
            unique.setdefault(item.tag, item)
        ordered = sorted(unique.values(), key=lambda candidate: (candidate.priority, candidate.rank))
        return ordered[:1]

    def _sentinel_tag(self, entity: dict, direction: str) -> str:
        system = self._normalize_token(str(entity.get("system") or "global")) or "global"
        prefix = "system_source" if direction == "upstream" else "system_sink"
        return f"{prefix}:{system}"

    def _engineering_metadata_extraction(self, entities: list[dict]) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for entity in entities:
            tag = self._normalize_token(entity["tag"])
            payload = entity.get("metadata") if isinstance(entity.get("metadata"), dict) else {}
            range_min = self._parse_float(payload.get("range_min") or payload.get("min") or payload.get("lrv"))
            range_max = self._parse_float(payload.get("range_max") or payload.get("max") or payload.get("urv"))
            out[tag] = {
                "current_value": payload.get("current_value"),
                "state": payload.get("state") or entity.get("status"),
                "setpoint": payload.get("setpoint") or payload.get("sp"),
                "mode": payload.get("mode") or entity.get("mode"),
                "unit": payload.get("unit") or payload.get("eng_unit"),
                "range_min": range_min,
                "range_max": range_max,
                "fail_state": payload.get("fail_state") or payload.get("safe_state"),
                "power": entity.get("power") or payload.get("power"),
            }
        return out

    def _traceability_mapping(
        self,
        entities: list[dict],
        context: dict[str, dict],
        relationships: dict[str, dict[str, set[str]]],
    ) -> dict[str, list[EngineeringTraceabilityItem]]:
        traces: dict[str, list[EngineeringTraceabilityItem]] = {}
        for entity in entities:
            tag = self._normalize_token(entity["tag"])
            trace_items: list[EngineeringTraceabilityItem] = []
            for doc in context.get(tag, {}).get("document_source", []):
                trace_items.append(
                    EngineeringTraceabilityItem(
                        source_type="document",
                        source_id=doc,
                        excerpt=entity.get("description"),
                        confidence=entity.get("node_confidence"),
                    )
                )
            for ref in entity.get("source_references", [])[:4]:
                trace_items.append(
                    EngineeringTraceabilityItem(
                        source_type="reference",
                        source_id=str(ref),
                        excerpt=str(ref),
                        confidence=entity.get("node_confidence"),
                    )
                )
            for relation_key, targets in relationships.get(tag, {}).items():
                if relation_key not in {"controls", "measures", "upstream", "downstream"}:
                    continue
                for target in sorted(targets)[:3]:
                    trace_items.append(
                        EngineeringTraceabilityItem(
                            source_type="relationship",
                            source_id=f"{tag}:{relation_key}:{target}",
                            excerpt=f"{tag} {relation_key} {target}",
                            confidence=0.72,
                        )
                    )
            traces[tag] = trace_items
        return traces

    def _derived_field_generation(
        self,
        entities: list[dict],
        relationships: dict[str, dict[str, set[str]]],
        loops: dict[str, list[str]],
        updown: dict[str, dict[str, list[str]]],
    ) -> dict[str, dict]:
        derived: dict[str, dict] = {}
        for entity in entities:
            tag = self._normalize_token(entity["tag"])
            rel = relationships.get(tag, {})
            controls = rel.get("controls", set())
            controlled_by = rel.get("controlled_by", set())
            connections = rel.get("connections", set())
            upstream = updown.get(tag, {}).get("upstream", [])
            downstream = updown.get(tag, {}).get("downstream", [])
            chain = loops.get(tag, [])

            derived[tag] = {
                "num_connections": len(connections),
                "num_upstream": len(upstream),
                "num_downstream": len(downstream),
                "control_chain": chain,
                "flow_chain": updown.get(tag, {}).get("flow_chain", [tag]),
                "is_orphan": False,
                "is_controlled": len(controlled_by) > 0,
                "is_actuated": len(controls) > 0,
                "inferred": bool(entity.get("is_synthetic")),
            }
        return derived

    def _row_building(
        self,
        entities: list[dict],
        context: dict[str, dict],
        relationships: dict[str, dict[str, set[str]]],
        loops: dict[str, list[str]],
        updown: dict[str, dict[str, list[str]]],
        metadata: dict[str, dict],
        traceability: dict[str, list[EngineeringTraceabilityItem]],
        derived: dict[str, dict],
        include_inferred: bool,
    ) -> list[EngineeringTableRow]:
        rows: list[EngineeringTableRow] = []

        for entity in sorted(entities, key=lambda item: str(item.get("tag", ""))):
            tag = self._normalize_token(entity["tag"])
            rel = relationships.get(tag, {})
            ctx = context.get(tag, {})
            meta = metadata.get(tag, {})
            drv = derived.get(tag, {})

            if not include_inferred and drv.get("inferred"):
                continue

            grounded_fields = {
                "tag": tag,
                "type": entity.get("type"),
                "description": entity.get("description"),
                "system": entity.get("system"),
                "document_source": ctx.get("document_source", []),
            }
            derived_fields = {
                "control_chain": drv.get("control_chain", []),
                "flow_chain": drv.get("flow_chain", []),
                "is_orphan": drv.get("is_orphan", False),
                "is_controlled": drv.get("is_controlled", False),
                "is_actuated": drv.get("is_actuated", False),
                "inferred": drv.get("inferred", False),
            }

            rows.append(
                EngineeringTableRow(
                    id=tag,
                    tag=tag,
                    type=str(entity.get("type") or "unknown"),
                    subtype=self._to_optional_string(entity.get("subtype")),
                    description=self._to_optional_string(entity.get("description")),
                    system=self._to_optional_string(entity.get("system")),
                    equipment=self._to_optional_string(entity.get("equipment")),
                    process_role=self._to_optional_string(entity.get("process_role")),
                    measures=sorted(rel.get("measures", set())),
                    controls=sorted(rel.get("controls", set())),
                    controlled_by=sorted(rel.get("controlled_by", set())),
                    signal_inputs=sorted(rel.get("signal_inputs", set())),
                    signal_outputs=sorted(rel.get("signal_outputs", set())),
                    upstream=updown.get(tag, {}).get("upstream", []),
                    downstream=updown.get(tag, {}).get("downstream", []),
                    upstream_links=updown.get(tag, {}).get("upstream_links", []),
                    downstream_links=updown.get(tag, {}).get("downstream_links", []),
                    has_inferred_upstream=bool(updown.get(tag, {}).get("has_inferred_upstream", False)),
                    has_inferred_downstream=bool(updown.get(tag, {}).get("has_inferred_downstream", False)),
                    flow_path=updown.get(tag, {}).get("flow_chain", [tag]),
                    current_value=self._to_optional_string(meta.get("current_value")),
                    state=self._to_optional_string(meta.get("state")),
                    setpoint=self._to_optional_string(meta.get("setpoint")),
                    mode=self._to_optional_string(meta.get("mode")),
                    unit=self._to_optional_string(meta.get("unit")),
                    range_min=meta.get("range_min"),
                    range_max=meta.get("range_max"),
                    fail_state=self._to_optional_string(meta.get("fail_state")),
                    power=self._to_optional_string(meta.get("power")),
                    document_source=list(ctx.get("document_source", [])),
                    line_reference=list(ctx.get("line_reference", [])),
                    confidence=max(0.35, min(0.99, float(entity.get("node_confidence") or 0.6))),
                    num_connections=int(drv.get("num_connections", 0)),
                    num_upstream=len(updown.get(tag, {}).get("upstream", [])),
                    num_downstream=len(updown.get(tag, {}).get("downstream", [])),
                    control_chain=loops.get(tag, drv.get("control_chain", [])),
                    flow_chain=drv.get("flow_chain", [tag]),
                    is_orphan=False,
                    is_controlled=bool(drv.get("is_controlled", False)),
                    is_actuated=bool(drv.get("is_actuated", False)),
                    warnings=[],
                    grounded_fields=grounded_fields,
                    derived_fields=derived_fields,
                    traceability=traceability.get(tag, []),
                )
            )

        return rows

    def _confidence_scoring(self, rows: list[EngineeringTableRow]) -> None:
        for row in rows:
            connection_factor = min(0.16, 0.02 * row.num_connections)
            traceability_factor = min(0.14, 0.02 * len(row.traceability))
            orphan_penalty = -0.08 if row.is_orphan else 0.0
            inferred_penalty = -0.06 if bool(row.derived_fields.get("inferred")) else 0.0
            score = row.confidence + connection_factor + traceability_factor + orphan_penalty + inferred_penalty
            row.confidence = round(max(0.3, min(0.99, score)), 3)

    def _annotate_row_warnings(self, rows: list[EngineeringTableRow]) -> None:
        for row in rows:
            row_warnings: list[str] = []
            if row.is_orphan:
                row_warnings.append("orphan node")
            if row.num_downstream == 0:
                row_warnings.append("no downstream")
            if row.num_upstream == 0:
                row_warnings.append("no upstream")
            if row.confidence < 0.55:
                row_warnings.append("low confidence")
            if bool(row.derived_fields.get("inferred")):
                row_warnings.append("inferred relationship")
            row.warnings = row_warnings

    def _quality_warnings(
        self,
        rows: list[EngineeringTableRow],
        relationships: dict[str, dict[str, set[str]]],
    ) -> list[EngineeringTableWarning]:
        warnings: list[EngineeringTableWarning] = []

        if len(rows) < 3:
            warnings.append(
                EngineeringTableWarning(
                    code="sparse_graph",
                    severity="warning",
                    message="Sparse engineering graph detected: fewer than 3 normalized entities.",
                    affected_tags=[row.tag for row in rows],
                )
            )

        missing_rel = [row.tag for row in rows if row.num_connections == 0]
        if missing_rel:
            warnings.append(
                EngineeringTableWarning(
                    code="missing_relationships",
                    severity="info",
                    message="Some entities required deterministic upstream/downstream completion beyond explicit relationships.",
                    affected_tags=missing_rel[:20],
                )
            )

        ambiguous = [tag for tag, rel in relationships.items() if len(rel.get("controlled_by", set())) > 2]
        if ambiguous:
            warnings.append(
                EngineeringTableWarning(
                    code="ambiguous_match",
                    severity="warning",
                    message="Multiple controllers point to the same target for some entities.",
                    affected_tags=ambiguous[:20],
                )
            )

        return warnings

    def _summary(self, rows: list[EngineeringTableRow]) -> EngineeringTableSummaryStats:
        confidences = [row.confidence for row in rows] or [0.0]
        distinct_systems = len({row.system for row in rows if row.system})
        distinct_sources = len({item for row in rows for item in row.document_source})
        grounded_rows = sum(1 for row in rows if not bool(row.derived_fields.get("inferred")))
        inferred_rows = len(rows) - grounded_rows

        return EngineeringTableSummaryStats(
            total_rows=len(rows),
            grounded_rows=grounded_rows,
            inferred_rows=inferred_rows,
            orphan_rows=sum(1 for row in rows if row.is_orphan),
            controlled_rows=sum(1 for row in rows if row.is_controlled),
            actuated_rows=sum(1 for row in rows if row.is_actuated),
            avg_confidence=round(mean(confidences), 3),
            distinct_systems=distinct_systems,
            distinct_document_sources=distinct_sources,
        )

    def _walk_graph(
        self,
        relationships: dict[str, dict[str, set[str]]],
        start: str,
        key: str,
        max_depth: int,
    ) -> list[str]:
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        visited: set[str] = {start}
        ordered: list[str] = []

        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor in sorted(relationships.get(node, {}).get(key, set())):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                ordered.append(neighbor)
                queue.append((neighbor, depth + 1))

        return ordered

    @staticmethod
    def _normalize_sentence(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _normalize_token(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_\-]", "", (value or "").strip())

    @staticmethod
    def _parse_float(value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_optional_string(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None


engineering_table_parser = EngineeringTableParser()
