from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from psycopg2.extras import Json

from db.postgres import postgres_client
from models.document_pipeline import DocumentParsingPipelineResult
from models.pipeline import DetectedTag, EngineeringEntity
from services.document_ingestion_service import document_ingestion_service
from services.deterministic_signal_extraction_service import deterministic_signal_extraction_service
from services.document_parsing_pipeline import parse_documents_pipeline
from services.engineering_inference import engineering_inference_service
from services.entity_classification_service import entity_classification_service
from services.graph_build_service import graph_build_service
from services.graph_layout_hint_service import graph_layout_hint_service
from services.graph_validation_service import graph_validation_service
from services.graph_service import graph_service
from services.narrative_extraction_service import narrative_extraction_service
from services.narrative_rule_extraction_service import narrative_rule_extraction_service
from services.behavior_loader_patch import load_parser_output_into_behavior_layer
from services.pid_parser import pid_parser_service
from services.pid_extraction_service import pid_extraction_service
from services.pid_reconciliation_service import pid_reconciliation_service
from services.process_unit_assignment_service import process_unit_assignment_service
from services.process_unit_detection_service import process_unit_detection_service
from services.project_service import project_service
from services.relationship_refinement_service import relationship_refinement_service
from services.relationship_inference_service import relationship_inference_service
from services.tag_normalization_service import tag_normalization_service
from services.validation_control_loop_layer import validation_control_loop_layer


class ParseService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _final_tag_payloads(pipeline_result: DocumentParsingPipelineResult) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for row in pipeline_result.final_validation.tag_rows:
            payload = row.model_dump()
            payload.update(
                {
                    "tag": row.tag,
                    "equipment": row.equipment,
                    "upstream": list(row.upstream),
                    "downstream": list(row.downstream),
                }
            )
            payloads.append(payload)
        return payloads

    @staticmethod
    def _final_loop_payloads(loops) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for loop in loops:
            payload = loop.model_dump()
            payload.update(
                {
                    "loop_id": loop.loop_id,
                    "sensor": loop.sensor_tag,
                    "actuator": loop.actuator_tag,
                    "process": loop.process_node,
                    "controller": loop.controller_tag,
                    "chain": list(loop.chain),
                    "confidence": float(loop.confidence),
                    "tuning_confidence": float(loop.tuning_confidence),
                }
            )
            payloads.append(payload)
        return payloads

    @staticmethod
    def _loop_definition_payloads(pipeline_result: DocumentParsingPipelineResult) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for loop in pipeline_result.final_validation.control_loops:
            payloads.append(
                {
                    "name": loop.name,
                    "source_sentence": " | ".join(loop.source_texts)[:400],
                    "page_number": 0,
                    "related_tags": [
                        tag
                        for tag in dict.fromkeys([*loop.chain, loop.sensor_tag, loop.controller_tag, loop.actuator_tag, loop.process_node])
                        if tag
                    ],
                    "confidence": loop.confidence,
                }
            )
        return payloads

    @staticmethod
    def _infer_document_type_from_name(file_name: str) -> str:
        lowered = file_name.lower()
        if any(token in lowered for token in ("p&id", "pid", "p_and_i", "p and i", "p_i_d", "p-i-d")):
            return "pid_pdf"
        if any(token in lowered for token in ("control narrative", "narrative", "control")):
            return "control_narrative"
        return "unknown_document"

    @staticmethod
    def _merge_metadata(
        base: dict[str, dict[str, object]],
        incoming: dict[str, dict[str, object]],
    ) -> dict[str, dict[str, object]]:
        for entity_id, payload in incoming.items():
            base.setdefault(entity_id, {})
            for key, value in payload.items():
                existing = base[entity_id].get(key)
                if isinstance(existing, list) and isinstance(value, list):
                    merged = [*existing]
                    for item in value:
                        if item not in merged:
                            merged.append(item)
                    base[entity_id][key] = merged
                elif isinstance(existing, dict) and isinstance(value, dict):
                    base[entity_id][key] = {**existing, **value}
                elif existing in (None, "", [], {}):
                    base[entity_id][key] = value
                else:
                    base[entity_id][key] = value
        return base

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
        pipeline_result: DocumentParsingPipelineResult,
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

        for tag in pipeline_result.structured_extraction.extracted_tags:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    tag.source_file_id,
                    "extracted_tag",
                    tag.normalized_tag,
                    Json(tag.model_dump()),
                    now,
                ),
            )

        for equipment in pipeline_result.structured_extraction.equipment_detections:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    equipment.source_file_id,
                    "normalized_equipment",
                    equipment.normalized_tag,
                    Json(equipment.model_dump()),
                    now,
                ),
            )

        for extracted_relationship in pipeline_result.structured_extraction.extracted_relationships:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    extracted_relationship.source_file_id,
                    "extracted_relationship",
                    f"{extracted_relationship.source_tag}->{extracted_relationship.target_tag}",
                    Json(extracted_relationship.model_dump()),
                    now,
                ),
            )

        for intent in pipeline_result.semantic_behavior.semantic_intents:
            postgres_client.execute(
                """
                INSERT INTO extracted_metadata (id, project_id, parse_batch_id, source_file_id, category, tag, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    parse_batch_id,
                    intent.source_file_id,
                    "semantic_intent",
                    intent.intent_id,
                    Json(intent.model_dump()),
                    now,
                ),
            )

        for chain in pipeline_result.semantic_behavior.behavioral_chains:
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
                    "behavioral_chain",
                    chain.chain_id,
                    Json(chain.model_dump()),
                    now,
                ),
            )

        for debug_item in pipeline_result.semantic_behavior.relationship_validation_debug:
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
                    "relationship_validation_debug",
                    debug_item.candidate_id,
                    Json(debug_item.model_dump()),
                    now,
                ),
            )

        for debug_item in pipeline_result.validation_control_loop.loop_validation_debug:
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
                    "loop_validation_debug",
                    debug_item.candidate_id,
                    Json(debug_item.model_dump()),
                    now,
                ),
            )

        for tuning_data in pipeline_result.final_validation.tuning_data:
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
                    "tuning_data",
                    tuning_data.tuning_id,
                    Json(tuning_data.model_dump()),
                    now,
                ),
            )

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
                "parser_relationship_graph",
                "validated",
                    Json(pipeline_result.final_validation.validated_graph.parser_graph.model_dump()),
                now,
            ),
        )

        for control_loop in self._loop_definition_payloads(pipeline_result):
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
                    control_loop["name"],
                    control_loop["source_sentence"],
                    control_loop["page_number"],
                    Json(control_loop["related_tags"]),
                    control_loop["confidence"],
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

        for loop in pipeline_result.final_validation.rejected_control_loops:
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
                    "rejected_control_loop",
                    loop.loop_id,
                    Json(loop.model_dump()),
                    now,
                ),
            )
            warnings.append(
                f"Rejected control loop {loop.loop_id}: support_count={loop.support_count} support={','.join(loop.support)}"
            )

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
                "final_validation_diagnostics",
                "summary",
                Json(pipeline_result.final_validation.diagnostics.model_dump()),
                now,
            ),
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
                "parse_job_id": "",
                "parse_batch_id": "",
                "parsed_at": datetime.now(timezone.utc).isoformat(),
                "summary": "No files available to parse for this project.",
                "documents_seen": 0,
                "documents": [],
                "document_types": [],
                "entities_count": 0,
                "nodes_count": 0,
                "edges_count": 0,
                "final_validation_diagnostics": {
                    "total_tags": 0,
                    "rejected_tags": 0,
                    "total_relationships": 0,
                    "rejected_relationships": 0,
                    "total_loops": 0,
                    "rejected_loops": 0,
                    "inferred_links": 0,
                    "duplicate_edges_removed": 0,
                    "duplicate_loops_removed": 0,
                },
                "unified_model": {
                    "tags": [],
                    "tag_rows": [],
                    "rejected_tag_rows": [],
                    "control_loops": [],
                    "rejected_control_loops": [],
                    "final_validation_diagnostics": {
                        "total_tags": 0,
                        "rejected_tags": 0,
                        "total_relationships": 0,
                        "rejected_relationships": 0,
                        "total_loops": 0,
                        "rejected_loops": 0,
                        "inferred_links": 0,
                        "duplicate_edges_removed": 0,
                        "duplicate_loops_removed": 0,
                    },
                },
                "warnings": [],
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
            warnings: list[str] = []
            ingested = document_ingestion_service.ingest_batch(files)
            if not ingested["pid_files"]:
                warnings.append("No P&ID documents in parse batch; process-flow edges may be incomplete.")
            if not ingested["narrative_files"]:
                warnings.append("No control narrative documents in parse batch; control semantics may be incomplete.")
            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="layer_1_structured_extraction",
                stage_message="Segmenting uploaded documents",
                progress_percent=15,
            )

            pipeline_result = parse_documents_pipeline(
                files,
                self._resolve_file_path,
                stage_callback=lambda stage, message, progress: self._update_parse_job_stage(
                    parse_job_id,
                    status="running",
                    current_stage=stage,
                    stage_message=message,
                    progress_percent=progress,
                ),
            )

            warnings.extend(pipeline_result.warnings)
            entities = pipeline_result.final_validation.validated_graph.entities
            process_units = pipeline_result.semantic_behavior.process_units
            relationships = pipeline_result.final_validation.validated_graph.relationships
            low_conf_relationships = pipeline_result.final_validation.validated_graph.rejected_relationships
            rule_bundle = pipeline_result.semantic_behavior.rule_bundle
            engineering_metadata = pipeline_result.semantic_behavior.metadata_by_entity

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="pid_reconciliation",
                stage_message="Reconciling normalized instrumentation against active plant graph",
                progress_percent=92,
            )
            reconcile_summary = pid_reconciliation_service.reconcile_from_entities(
                project_id=project_id,
                entities=entities,
                relationships=relationships,
                similarity_threshold=0.9,
            )
            warnings.extend(
                [
                    f"P&ID reconcile conflict: {item.incoming_tag} vs {item.existing_tag} ({item.similarity})"
                    for item in reconcile_summary.possible_conflicts
                ]
            )

            entities = graph_layout_hint_service.assign(entities, process_units)

            self._update_parse_job_stage(
                parse_job_id,
                status="running",
                current_stage="graph_build",
                stage_message="Building and persisting plant graph",
                progress_percent=94,
            )
            nodes, edges = graph_build_service.build(entities, relationships, deep_metadata=engineering_metadata)
            graph_service.store_graph(project_id, nodes, edges)

            try:
                behavior_load_result = load_parser_output_into_behavior_layer(
                    project_id=project_id,
                    rows=None,
                    edges=[dict(edge) for edge in edges],
                    file_ids=file_ids or [],
                    include_inferred=True,
                    max_flow_depth=4,
                )
                self.logger.info(
                    "parse_behavior_load project_id=%s rows_loaded=%s edges_loaded=%s sample_tags=%s",
                    project_id,
                    behavior_load_result.get("rows"),
                    behavior_load_result.get("edges"),
                    behavior_load_result.get("sample_tags", []),
                )
            except Exception as behavior_exc:
                warnings.append(f"Behavior layer load skipped: {behavior_exc}")

            self._store_batch_artifacts(
                project_id=project_id,
                parse_batch_id=parse_batch_id,
                files=files,
                entities=entities,
                relationships=relationships,
                low_confidence_relationships=low_conf_relationships,
                rule_bundle=rule_bundle,
                pipeline_result=pipeline_result,
                warnings=warnings,
            )

            completed_at = datetime.now(timezone.utc)
            tag_payloads = self._final_tag_payloads(pipeline_result)
            control_loop_payloads = self._final_loop_payloads(pipeline_result.final_validation.control_loops)
            rejected_loop_payloads = self._final_loop_payloads(pipeline_result.final_validation.rejected_control_loops)
            unified_model = {
            "equipment": [entity.id for entity in entities if entity.canonical_type in {"pump", "valve", "control_valve", "blower", "tank", "basin", "clarifier", "chemical_system_device", "generic_device"}],
            "instruments": [entity.id for entity in entities if entity.canonical_type in {"flow_transmitter", "level_transmitter", "level_switch", "pressure_transmitter", "differential_pressure_transmitter", "temperature_transmitter", "analyzer"}],
            "tags": tag_payloads,
            "tag_rows": tag_payloads,
            "rejected_tag_rows": [item.model_dump() for item in pipeline_result.final_validation.rejected_tag_rows],
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
            "control_loops": control_loop_payloads,
            "control_loop_visibility_threshold": validation_control_loop_layer.DEFAULT_VISIBLE_LOOP_CONFIDENCE_THRESHOLD,
            "interlocks": [item.model_dump() for item in rule_bundle.get("interlocks", [])],
            "alarms": [item.model_dump() for item in rule_bundle.get("alarms", [])],
            "sequences": {
                "startup": [item.model_dump() for item in rule_bundle.get("sequences", []) if item.sequence_type == "startup"],
                "shutdown": [item.model_dump() for item in rule_bundle.get("sequences", []) if item.sequence_type == "shutdown"],
            },
            "operating_modes": [item.model_dump() for item in rule_bundle.get("modes", [])],
            "semantic_intents": [item.model_dump() for item in pipeline_result.semantic_behavior.semantic_intents],
            "normalized_intents": [item.model_dump() for item in pipeline_result.semantic_behavior.normalized_intents],
            "behavioral_chains": [item.model_dump() for item in pipeline_result.semantic_behavior.behavioral_chains],
            "rejected_relationships": [item.model_dump() for item in pipeline_result.final_validation.validated_graph.rejected_relationships],
            "relationship_graph": pipeline_result.final_validation.validated_graph.parser_graph.model_dump(),
            "tuning_data": [item.model_dump() for item in pipeline_result.final_validation.tuning_data],
            "rejected_control_loops": rejected_loop_payloads,
            "relationship_validation_debug": [item.model_dump() for item in pipeline_result.semantic_behavior.relationship_validation_debug],
            "loop_validation_debug": [item.model_dump() for item in pipeline_result.validation_control_loop.loop_validation_debug],
            "final_validation_diagnostics": pipeline_result.final_validation.diagnostics.model_dump(),
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
            "validated_tag_rows_count": len(pipeline_result.final_validation.tag_rows),
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "final_validation_diagnostics": pipeline_result.final_validation.diagnostics.model_dump(),
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
            "final_validation_diagnostics": pipeline_result.final_validation.diagnostics.model_dump(),
            "unified_model": unified_model,
            "summary": "Deterministic engineering parse completed: staged extraction, normalization, graph reconstruction, and final response validation.",
            "pipeline_stages": [
                "layer_1_structured_extraction",
                "layer_2_semantic_behavior",
                "layer_3_validation_control_loop",
                "layer_4_final_validation",
            ],
        }


parse_service = ParseService()
