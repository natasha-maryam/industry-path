from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from psycopg2.extras import Json

from db.postgres import postgres_client
from models.pipeline import DetectedTag, EngineeringEntity
from services.document_ingestion_service import document_ingestion_service
from services.entity_classification_service import entity_classification_service
from services.graph_build_service import graph_build_service
from services.graph_layout_hint_service import graph_layout_hint_service
from services.graph_validation_service import graph_validation_service
from services.graph_service import graph_service
from services.narrative_extraction_service import narrative_extraction_service
from services.narrative_rule_extraction_service import narrative_rule_extraction_service
from services.pid_extraction_service import pid_extraction_service
from services.process_unit_assignment_service import process_unit_assignment_service
from services.process_unit_detection_service import process_unit_detection_service
from services.project_service import project_service
from services.relationship_refinement_service import relationship_refinement_service
from services.relationship_inference_service import relationship_inference_service
from services.tag_normalization_service import tag_normalization_service


class ParseService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _infer_document_type_from_name(file_name: str) -> str:
        lowered = file_name.lower()
        if any(token in lowered for token in ("p&id", "pid", "p_and_i", "p and i", "p_i_d", "p-i-d")):
            return "pid_pdf"
        if any(token in lowered for token in ("control narrative", "narrative", "control")):
            return "control_narrative"
        return "unknown_document"

    def _project_files(self, project_id: str, file_ids: list[str] | None = None) -> list[dict]:
        params: list[object] = [project_id]
        where_clause = "WHERE project_id = %s"
        if file_ids:
            where_clause += " AND id::text = ANY(%s)"
            params.append(file_ids)

        rows = postgres_client.fetch_all(
            f"""
            SELECT id::text AS id,
                   original_name,
                   stored_name,
                   file_type,
                   document_type,
                   file_path,
                   uploaded_at
            FROM project_files
            {where_clause}
            ORDER BY uploaded_at ASC
            """,
            tuple(params),
        )

        for row in rows:
            declared = row.get("document_type", "unknown_document")
            if declared == "unknown_document":
                row["document_type"] = self._infer_document_type_from_name(row["original_name"])
        return rows

    def _next_batch_name(self, project_id: str) -> str:
        row = postgres_client.fetch_one(
            "SELECT COUNT(*) AS count FROM parse_batches WHERE project_id = %s",
            (project_id,),
        )
        count = int(row["count"]) if row and row.get("count") is not None else 0
        return f"Batch {count + 1:03d}"

    @staticmethod
    def _resolve_file_path(relative_file_path: str) -> Path:
        workspace_root = Path(__file__).resolve().parents[2]
        return (workspace_root / relative_file_path).resolve()

    def _detect_tags(self, chunks) -> list[DetectedTag]:
        tags: list[DetectedTag] = []
        for chunk in chunks:
            detections = tag_normalization_service.detect_tags(chunk.text)
            for item in detections:
                confidence = 0.9 if chunk.document_type == "pid_pdf" else 0.82
                if chunk.ocr_used:
                    confidence -= 0.08
                tags.append(
                    DetectedTag(
                        normalized_tag=item["normalized_tag"],
                        raw_tag=item["raw_tag"],
                        family=item["family"],
                        canonical_type=item["canonical_type"],
                        source_file_id=chunk.file_id,
                        source_file_name=chunk.file_name,
                        source_page=chunk.page_number,
                        source_text=chunk.text[:400],
                        confidence=max(0.3, confidence),
                    )
                )
        self.logger.info("Detected %s raw tags", len(tags))
        return tags

    def _store_batch_artifacts(
        self,
        project_id: str,
        parse_batch_id: str,
        files: list[dict],
        entities,
        relationships,
        low_confidence_relationships,
        rule_bundle: dict[str, list],
        warnings: list[str],
    ) -> None:
        now = datetime.now(timezone.utc)

        for item in files:
            postgres_client.execute(
                """
                INSERT INTO parse_batch_files (id, parse_batch_id, file_id, document_type, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(uuid4()), parse_batch_id, item["id"], item.get("document_type", "unknown_document"), now),
            )

        for entity in entities:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    None,
                    "engineering_entity",
                    entity.id,
                    Json(entity.model_dump()),
                    now,
                ),
            )

        for rel in relationships:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    None,
                    "inferred_relationship",
                    f"{rel.source_entity}->{rel.target_entity}",
                    Json(rel.model_dump()),
                    now,
                ),
            )

        for control_loop in rule_bundle.get("control_loops", []):
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
                    control_loop.name,
                    control_loop.source_sentence,
                    control_loop.page_number,
                    Json(control_loop.related_tags),
                    control_loop.confidence,
                    now,
                ),
            )

        for alarm in rule_bundle.get("alarms", []):
            postgres_client.execute(
                """
                INSERT INTO alarm_definitions (
                    id, project_id, parse_batch_id, name, source_sentence, page_number, related_tags, confidence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    alarm.name,
                    alarm.source_sentence,
                    alarm.page_number,
                    Json(alarm.related_tags),
                    alarm.confidence,
                    now,
                ),
            )

        for interlock in rule_bundle.get("interlocks", []):
            postgres_client.execute(
                """
                INSERT INTO interlock_definitions (
                    id, project_id, parse_batch_id, name, source_sentence, page_number, related_tags, confidence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    interlock.name,
                    interlock.source_sentence,
                    interlock.page_number,
                    Json(interlock.related_tags),
                    interlock.confidence,
                    now,
                ),
            )

        for rel in low_confidence_relationships:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    None,
                    "low_confidence_relationship",
                    f"{rel.source_entity}->{rel.target_entity}",
                    Json(rel.model_dump()),
                    now,
                ),
            )
            warnings.append(
                f"LOW edge suggestion {rel.source_entity} {rel.relationship_type} {rel.target_entity}: {rel.explanation}"
            )

        for warning in warnings:
            postgres_client.execute(
                """
                INSERT INTO parse_conflicts (id, project_id, parse_batch_id, conflict_type, tag, details, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid4()), project_id, parse_batch_id, "warning", None, warning, now),
            )

    def _update_parse_job_stage(
        self,
        parse_job_id: str,
        *,
        status: str,
        current_stage: str,
        stage_message: str,
        progress_percent: float,
        error_message: str | None = None,
    ) -> None:
        postgres_client.execute(
            """
            UPDATE parse_jobs
            SET status = %s,
                current_stage = %s,
                stage_message = %s,
                progress_percent = %s,
                error_message = %s
            WHERE id = %s
            """,
            (status, current_stage, stage_message, progress_percent, error_message, parse_job_id),
        )

    def get_parse_job_status(self, project_id: str, parse_job_id: str) -> dict[str, object]:
        project_service.ensure_project(project_id)
        row = postgres_client.fetch_one(
            """
            SELECT id::text AS parse_job_id,
                   project_id::text AS project_id,
                   parse_batch_id::text AS parse_batch_id,
                   status,
                   current_stage,
                   stage_message,
                   progress_percent,
                   nodes_count,
                   edges_count,
                   started_at,
                   completed_at,
                   error_message
            FROM parse_jobs
            WHERE id = %s AND project_id = %s
            """,
            (parse_job_id, project_id),
        )
        if row is None:
            return {
                "parse_job_id": parse_job_id,
                "project_id": project_id,
                "status": "not_found",
                "current_stage": None,
                "stage_message": "Parse job not found.",
                "progress_percent": 0.0,
                "nodes_count": 0,
                "edges_count": 0,
                "started_at": None,
                "completed_at": None,
                "error_message": None,
            }

        return {
            **row,
            "progress_percent": float(row.get("progress_percent") or 0.0),
            "started_at": row.get("started_at").isoformat() if row.get("started_at") else None,
            "completed_at": row.get("completed_at").isoformat() if row.get("completed_at") else None,
        }

    def get_low_confidence_suggestions(self, project_id: str, parse_batch_id: str) -> dict[str, object]:
        project_service.ensure_project(project_id)
        rows = postgres_client.fetch_all(
            """
            SELECT payload
            FROM extracted_metadata
            WHERE project_id = %s
              AND parse_batch_id = %s
              AND category = 'low_confidence_relationship'
            ORDER BY created_at ASC
            """,
            (project_id, parse_batch_id),
        )
        return {
            "project_id": project_id,
            "parse_batch_id": parse_batch_id,
            "suggestions": [row["payload"] for row in rows],
        }

    def parse_project(self, project_id: str, file_ids: list[str] | None = None) -> dict[str, object]:
        project_service.ensure_project(project_id)
        files = self._project_files(project_id, file_ids=file_ids)
        if not files:
            return {
                "project_id": project_id,
                "summary": "No files available to parse for this project.",
                "documents_seen": 0,
                "nodes_count": 0,
                "edges_count": 0,
            }

        parse_batch_id = str(uuid4())
        parse_job_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        batch_name = self._next_batch_name(project_id)

        postgres_client.execute(
            """
            INSERT INTO parse_batches (id, project_id, batch_name, status, started_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (parse_batch_id, project_id, batch_name, "running", started_at),
        )
        postgres_client.execute(
            """
            INSERT INTO parse_jobs (id, project_id, parse_batch_id, status, current_stage, stage_message, progress_percent, started_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (parse_job_id, project_id, parse_batch_id, "running", "ingestion", "Reading parse batch files", 5, started_at),
        )

        try:
            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="ingestion",
                stage_message="Classifying uploaded documents",
                progress_percent=10,
            )

            ingested = document_ingestion_service.ingest_batch(files)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="raw_extraction",
                stage_message="Extracting text and OCR chunks",
                progress_percent=25,
            )
            pid_chunks = pid_extraction_service.extract(ingested["pid_files"], self._resolve_file_path)
            narrative_chunks = narrative_extraction_service.extract(ingested["narrative_files"], self._resolve_file_path)

            warnings: list[str] = []
            if not ingested["pid_files"]:
                warnings.append("No P&ID documents in parse batch; process-flow edges may be incomplete.")
            if not ingested["narrative_files"]:
                warnings.append("No control narrative documents in parse batch; control semantics may be incomplete.")

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="tag_detection",
                stage_message="Detecting and normalizing engineering tags",
                progress_percent=45,
            )
            all_chunks = [*pid_chunks, *narrative_chunks]
            detected_tags = self._detect_tags(all_chunks)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="entity_classification",
                stage_message="Building normalized engineering entities",
                progress_percent=58,
            )
            entities = entity_classification_service.build_entities(detected_tags)
            narrative_blob = "\n".join(chunk.text for chunk in narrative_chunks)
            entities = entity_classification_service.assign_process_units(entities, narrative_blob)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="process_unit_detection",
                stage_message="Detecting process-unit topology nodes",
                progress_percent=62,
            )
            process_units, synthetic_nodes = process_unit_detection_service.detect(
                pid_chunks=pid_chunks,
                narrative_chunks=narrative_chunks,
                entities=entities,
            )

            for unit in process_units:
                entities.append(
                    EngineeringEntity(
                        id=unit.id,
                        tag=unit.id,
                        canonical_type="process_unit",
                        display_name=unit.name,
                        aliases=unit.aliases,
                        process_unit=unit.id,
                        source_documents=[],
                        source_pages=[],
                        source_snippets=[],
                        confidence=unit.confidence,
                        is_synthetic=True,
                        explanation=f"Process unit node ({unit.canonical_type})",
                        source_references=unit.source_references,
                        parse_notes=["Detected process unit node"],
                    )
                )

            for synthetic in synthetic_nodes:
                entities.append(
                    EngineeringEntity(
                        id=synthetic.id,
                        tag=synthetic.id,
                        canonical_type=synthetic.canonical_type,
                        display_name=synthetic.label,
                        aliases=[],
                        process_unit=synthetic.process_unit,
                        source_documents=[],
                        source_pages=[],
                        source_snippets=[],
                        confidence=synthetic.confidence,
                        is_synthetic=True,
                        explanation=synthetic.explanation,
                        source_references=synthetic.source_references,
                        parse_notes=["Synthetic topology node"],
                    )
                )

            entities, part_of_relationships, assignment_warnings = process_unit_assignment_service.assign(
                entities=entities,
                process_units=process_units,
            )
            warnings.extend(assignment_warnings)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="narrative_rules",
                stage_message="Extracting control loops, alarms, and interlocks",
                progress_percent=68,
            )
            rule_bundle = narrative_rule_extraction_service.extract_rules(narrative_chunks)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="relationship_inference",
                stage_message="Inferring engineering relationships",
                progress_percent=78,
            )
            relationships, low_conf_relationships, rel_warnings = relationship_inference_service.infer(
                entities=entities,
                rule_bundle=rule_bundle,
                pid_chunks=pid_chunks,
            )
            warnings.extend(rel_warnings)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="relationship_refinement",
                stage_message="Refining engineering edge semantics and directionality",
                progress_percent=84,
            )
            relationships = relationship_refinement_service.refine(
                entities=entities,
                process_units=process_units,
                base_relationships=[*relationships, *part_of_relationships],
                rule_bundle=rule_bundle,
            )

            relationships, validation_warnings, validation_low = graph_validation_service.validate(
                entities=entities,
                relationships=relationships,
            )
            low_conf_relationships.extend(validation_low)
            warnings.extend([item.message for item in validation_warnings])

            entities = graph_layout_hint_service.assign(entities, process_units)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="graph_build",
                stage_message="Building and persisting plant graph",
                progress_percent=90,
            )
            nodes, edges = graph_build_service.build(entities, relationships)
            graph_service.store_graph(project_id, nodes, edges)

            self._store_batch_artifacts(
                project_id=project_id,
                parse_batch_id=parse_batch_id,
                files=files,
                entities=entities,
                relationships=relationships,
                low_confidence_relationships=low_conf_relationships,
                rule_bundle=rule_bundle,
                warnings=warnings,
            )

            completed_at = datetime.now(timezone.utc)
            unified_model = {
            "equipment": [entity.id for entity in entities if entity.canonical_type in {"pump", "valve", "control_valve", "blower", "tank", "basin", "clarifier", "chemical_system_device", "generic_device"}],
            "instruments": [entity.id for entity in entities if entity.canonical_type in {"flow_transmitter", "level_transmitter", "level_switch", "pressure_transmitter", "differential_pressure_transmitter", "analyzer"}],
            "process_units": [
                {
                    "id": unit.id,
                    "name": unit.name,
                    "canonical_type": unit.canonical_type,
                    "confidence": unit.confidence,
                    "source_references": unit.source_references,
                }
                for unit in process_units
            ],
            "process_flow_relationships": [edge for edge in edges if edge["edge_type"] in {"PROCESS_FLOW", "FEEDS", "DISCHARGES_TO", "CONNECTED_TO"}],
            "signal_control_relationships": [edge for edge in edges if edge["edge_type"] in {"SIGNAL_TO", "CONTROLS", "MEASURES", "MONITORS", "SUPPLIES_AIR_TO"}],
            "control_loops": [item.model_dump() for item in rule_bundle.get("control_loops", [])],
            "interlocks": [item.model_dump() for item in rule_bundle.get("interlocks", [])],
            "alarms": [item.model_dump() for item in rule_bundle.get("alarms", [])],
            "sequences": {
                "startup": [item.model_dump() for item in rule_bundle.get("sequences", []) if item.sequence_type == "startup"],
                "shutdown": [item.model_dump() for item in rule_bundle.get("sequences", []) if item.sequence_type == "shutdown"],
            },
            "operating_modes": [item.model_dump() for item in rule_bundle.get("modes", [])],
            "clusters": [
                {
                    "cluster_id": entity.cluster_id,
                    "cluster_name": entity.cluster_name,
                    "cluster_order": entity.cluster_order,
                    "preferred_direction": entity.preferred_direction,
                    "node_id": entity.id,
                }
                for entity in entities
                if entity.cluster_id
            ],
        }

            summary_payload = {
            "documents_seen": len(files),
            "document_types": sorted({item.get("document_type", "unknown_document") for item in files}),
            "entities_count": len(entities),
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "warnings_count": len(warnings),
        }

            postgres_client.execute(
            """
            UPDATE parse_batches
            SET status = %s,
                completed_at = %s,
                summary = %s,
                warnings = %s
            WHERE id = %s
            """,
            ("completed", completed_at, Json(summary_payload), Json(warnings), parse_batch_id),
        )

            postgres_client.execute(
            """
            UPDATE parse_jobs
            SET status = %s,
                current_stage = %s,
                stage_message = %s,
                progress_percent = %s,
                nodes_count = %s,
                edges_count = %s,
                completed_at = %s
            WHERE id = %s
            """,
            ("completed", "completed", "Parse completed", 100, len(nodes), len(edges), completed_at, parse_job_id),
        )

        except Exception as exc:
            self._update_parse_job_stage(
                parse_job_id,
                status="failed",
                current_stage="failed",
                stage_message="Parse pipeline failed",
                progress_percent=100,
                error_message=str(exc),
            )
            postgres_client.execute(
                """
                UPDATE parse_batches
                SET status = %s,
                    completed_at = %s,
                    warnings = %s
                WHERE id = %s
                """,
                ("failed", datetime.now(timezone.utc), Json([f"Pipeline failed: {exc}"]), parse_batch_id),
            )
            raise

        return {
            "project_id": project_id,
            "parse_job_id": parse_job_id,
            "parse_batch_id": parse_batch_id,
            "parsed_at": completed_at.isoformat(),
            "documents_seen": len(files),
            "documents": [item["original_name"] for item in files],
            "document_types": [item.get("document_type", "unknown_document") for item in files],
            "entities_count": len(entities),
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "warnings": warnings,
            "unified_model": unified_model,
            "summary": "Deterministic engineering parse completed: staged extraction, normalization, rule inference, and graph build.",
        }


parse_service = ParseService()
