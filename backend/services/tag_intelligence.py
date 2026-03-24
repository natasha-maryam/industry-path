from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.deterministic_behavior_service import deterministic_behavior_service
from services.graph_service import graph_service
from services.uns_core import uns_core


@dataclass(slots=True)
class TagIntelligenceRow:
    tag: str
    tag_type: str | None
    equipment: str | None
    sources: list[str]
    inbound_count: int
    outbound_count: int
    relation_count: int
    is_unused: bool
    is_orphan: bool
    conflicts: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "tag_type": self.tag_type,
            "equipment": self.equipment,
            "sources": self.sources,
            "inbound_count": self.inbound_count,
            "outbound_count": self.outbound_count,
            "relation_count": self.relation_count,
            "is_unused": self.is_unused,
            "is_orphan": self.is_orphan,
            "conflicts": self.conflicts,
        }


class TagIntelligenceService:
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _to_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _collect_edges(self, project_id: str | None = None) -> list[dict[str, Any]]:
        edges = deterministic_behavior_service.get_edges()
        if edges:
            return edges

        if project_id:
            try:
                graph = graph_service.get_graph(project_id)
                return [edge.model_dump() if hasattr(edge, "model_dump") else dict(edge) for edge in graph.edges]
            except Exception:
                pass

        return uns_core.get_edges()

    def build_tag_database(self, project_id: str | None = None) -> dict[str, Any]:
        behavior_rows = deterministic_behavior_service.get_rows()
        uns_rows = uns_core.get_rows()
        edges = self._collect_edges(project_id)

        tag_info: dict[str, dict[str, Any]] = {}
        type_values: dict[str, set[str]] = defaultdict(set)
        equipment_values: dict[str, set[str]] = defaultdict(set)
        inbound: dict[str, set[str]] = defaultdict(set)
        outbound: dict[str, set[str]] = defaultdict(set)

        def ensure_tag(tag: str) -> dict[str, Any]:
            if tag not in tag_info:
                tag_info[tag] = {
                    "tag": tag,
                    "tag_type": None,
                    "equipment": None,
                    "sources": set(),
                    "controls": set(),
                    "upstream": set(),
                    "downstream": set(),
                }
            return tag_info[tag]

        for row in behavior_rows:
            tag = self._to_text(row.get("tag"))
            if not tag:
                continue
            item = ensure_tag(tag)
            item["sources"].add("behavior")

            row_type = self._to_text(row.get("type"))
            if row_type:
                type_values[tag].add(row_type)
                item["tag_type"] = item["tag_type"] or row_type

            equipment = self._to_text(row.get("equipment"))
            if equipment:
                equipment_values[tag].add(equipment)
                item["equipment"] = item["equipment"] or equipment

            for key in ("controls", "upstream", "downstream"):
                values = row.get(key) or []
                if isinstance(values, list):
                    for value in values:
                        value_text = self._to_text(value)
                        if value_text:
                            item[key].add(value_text)

        for row in uns_rows:
            tag = self._to_text(row.get("tag"))
            if not tag:
                continue
            item = ensure_tag(tag)
            item["sources"].add("uns")

            row_type = self._to_text(row.get("type"))
            if row_type:
                type_values[tag].add(row_type)
                item["tag_type"] = item["tag_type"] or row_type

            equipment = self._to_text(row.get("equipment"))
            if equipment:
                equipment_values[tag].add(equipment)
                item["equipment"] = item["equipment"] or equipment

            for key in ("controls", "upstream", "downstream"):
                values = row.get(key) or []
                if isinstance(values, list):
                    for value in values:
                        value_text = self._to_text(value)
                        if value_text:
                            item[key].add(value_text)

        for edge in edges:
            source = self._to_text(edge.get("source"))
            target = self._to_text(edge.get("target"))
            if not source or not target:
                continue
            ensure_tag(source)
            ensure_tag(target)
            outbound[source].add(target)
            inbound[target].add(source)

        rows: list[TagIntelligenceRow] = []
        for tag in sorted(tag_info.keys()):
            info = tag_info[tag]
            inbound_count = len(inbound.get(tag, set()))
            outbound_count = len(outbound.get(tag, set()))
            relation_count = len(info["controls"]) + len(info["upstream"]) + len(info["downstream"]) + inbound_count + outbound_count

            conflicts: list[str] = []
            if len(type_values.get(tag, set())) > 1:
                conflicts.append(f"Type mismatch: {sorted(type_values[tag])}")
            if len(equipment_values.get(tag, set())) > 1:
                conflicts.append(f"Equipment mismatch: {sorted(equipment_values[tag])}")

            is_orphan = inbound_count == 0 and outbound_count == 0
            is_unused = relation_count == 0

            row = TagIntelligenceRow(
                tag=tag,
                tag_type=info["tag_type"],
                equipment=info["equipment"],
                sources=sorted(str(item) for item in info["sources"]),
                inbound_count=inbound_count,
                outbound_count=outbound_count,
                relation_count=relation_count,
                is_unused=is_unused,
                is_orphan=is_orphan,
                conflicts=conflicts,
            )
            rows.append(row)

        return {
            "project_id": project_id,
            "rows": [row.as_dict() for row in rows],
            "summary": {
                "total": len(rows),
                "unused": sum(1 for row in rows if row.is_unused),
                "orphans": sum(1 for row in rows if row.is_orphan),
                "conflicts": sum(1 for row in rows if len(row.conflicts) > 0),
            },
            "timestamp": self._now(),
        }

    def query_rows(self, project_id: str | None = None, category: str = "all", search: str = "") -> dict[str, Any]:
        payload = self.build_tag_database(project_id)
        rows = payload["rows"] if isinstance(payload.get("rows"), list) else []

        category_value = (category or "all").strip().lower()
        filtered: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue

            include = True
            if category_value == "unused":
                include = bool(row.get("is_unused"))
            elif category_value == "orphans":
                include = bool(row.get("is_orphan"))
            elif category_value == "conflicts":
                include = len(row.get("conflicts", [])) > 0

            if include and search.strip():
                search_text = search.strip().lower()
                haystack = " ".join(
                    [
                        str(row.get("tag") or ""),
                        str(row.get("tag_type") or ""),
                        str(row.get("equipment") or ""),
                        " ".join(str(item) for item in row.get("sources", [])),
                        " ".join(str(item) for item in row.get("conflicts", [])),
                    ]
                ).lower()
                include = search_text in haystack

            if include:
                filtered.append(row)

        return {
            "project_id": project_id,
            "category": category_value,
            "search": search,
            "rows": filtered,
            "summary": payload.get("summary", {}),
            "timestamp": payload.get("timestamp"),
        }

    def export_csv(self, project_id: str | None = None, category: str = "all", search: str = "") -> bytes:
        payload = self.query_rows(project_id=project_id, category=category, search=search)
        rows = payload.get("rows", []) if isinstance(payload, dict) else []

        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "tag",
                "tag_type",
                "equipment",
                "sources",
                "inbound_count",
                "outbound_count",
                "relation_count",
                "is_unused",
                "is_orphan",
                "conflicts",
            ],
        )
        writer.writeheader()
        for row in rows:
            if not isinstance(row, dict):
                continue
            writer.writerow(
                {
                    "tag": row.get("tag"),
                    "tag_type": row.get("tag_type"),
                    "equipment": row.get("equipment"),
                    "sources": ";".join(str(item) for item in row.get("sources", [])),
                    "inbound_count": row.get("inbound_count"),
                    "outbound_count": row.get("outbound_count"),
                    "relation_count": row.get("relation_count"),
                    "is_unused": row.get("is_unused"),
                    "is_orphan": row.get("is_orphan"),
                    "conflicts": ";".join(str(item) for item in row.get("conflicts", [])),
                }
            )

        return buffer.getvalue().encode("utf-8")

    def export_json(self, project_id: str | None = None, category: str = "all", search: str = "") -> bytes:
        payload = self.query_rows(project_id=project_id, category=category, search=search)
        return json.dumps(payload, indent=2, default=str).encode("utf-8")


tag_intelligence_service = TagIntelligenceService()
