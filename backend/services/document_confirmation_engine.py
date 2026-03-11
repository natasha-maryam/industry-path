from __future__ import annotations

import logging
import re

from db.postgres import postgres_client
from models.logic import (
    CompletedLogicModel,
    DocumentConfirmationItem,
    DocumentConfirmationResult,
)
from models.pipeline import EngineeringEntity


class DocumentConfirmationEngine:
    """Cross-check generated logic model against extracted document evidence."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _latest_parse_batch_id(project_id: str) -> str | None:
        row = postgres_client.fetch_one(
            """
            SELECT id::text AS id
            FROM parse_batches
            WHERE project_id = %s
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (project_id,),
        )
        return str(row.get("id")) if row else None

    @staticmethod
    def _fetch_definition_rows(project_id: str, parse_batch_id: str, table: str) -> list[dict]:
        return postgres_client.fetch_all(
            f"""
            SELECT name, source_sentence, page_number, related_tags, confidence
            FROM {table}
            WHERE project_id = %s AND parse_batch_id = %s
            ORDER BY confidence DESC, created_at DESC
            """,
            (project_id, parse_batch_id),
        )

    @staticmethod
    def _fetch_relationship_rows(project_id: str, parse_batch_id: str) -> list[dict]:
        rows = postgres_client.fetch_all(
            """
            SELECT payload
            FROM extracted_metadata
            WHERE project_id = %s
              AND parse_batch_id = %s
              AND category = 'inferred_relationship'
            ORDER BY created_at DESC
            """,
            (project_id, parse_batch_id),
        )
        payloads: list[dict] = []
        for row in rows:
            payload = row.get("payload")
            if isinstance(payload, dict):
                payloads.append(payload)
        return payloads

    @staticmethod
    def _related_tags(row: dict) -> list[str]:
        tags = row.get("related_tags") or []
        normalized: list[str] = []
        for tag in tags:
            if not tag:
                continue
            normalized.append(str(tag).upper())
        return normalized

    @staticmethod
    def _row_reference(row: dict, source: str) -> str:
        page = row.get("page_number")
        if page is None:
            return source
        return f"{source} page {page}"

    @staticmethod
    def _any_pattern(text: str, patterns: list[str]) -> bool:
        lowered = text.lower()
        return any(pattern in lowered for pattern in patterns)

    @staticmethod
    def _entity_evidence(entities: list[EngineeringEntity], tag: str) -> list[str]:
        needle = (tag or "").upper()
        evidence: list[str] = []
        if not needle:
            return evidence
        for entity in entities:
            snippets = entity.source_snippets or []
            for snippet in snippets:
                if needle in snippet.upper() or entity.id.upper() == needle:
                    evidence.append(snippet)
        return evidence

    @staticmethod
    def _match_by_tags(rows: list[dict], required_tags: list[str], minimum_matches: int) -> dict | None:
        required = [tag.upper() for tag in required_tags if tag]
        if not required:
            return None

        best_row: dict | None = None
        best_score = -1
        for row in rows:
            row_tags = set(DocumentConfirmationEngine._related_tags(row))
            score = sum(1 for tag in required if tag.upper() in row_tags)
            if score >= minimum_matches and score > best_score:
                best_row = row
                best_score = score
        return best_row

    def confirm(
        self,
        project_id: str,
        entities: list[EngineeringEntity],
        model: CompletedLogicModel,
    ) -> tuple[CompletedLogicModel, DocumentConfirmationResult]:
        parse_batch_id = self._latest_parse_batch_id(project_id)
        loop_rows: list[dict] = []
        alarm_rows: list[dict] = []
        interlock_rows: list[dict] = []
        relationship_rows: list[dict] = []

        if parse_batch_id:
            loop_rows = self._fetch_definition_rows(project_id, parse_batch_id, "control_loop_definitions")
            alarm_rows = self._fetch_definition_rows(project_id, parse_batch_id, "alarm_definitions")
            interlock_rows = self._fetch_definition_rows(project_id, parse_batch_id, "interlock_definitions")
            relationship_rows = self._fetch_relationship_rows(project_id, parse_batch_id)

        confirmed_loop_pairs: set[tuple[str, str]] = set()

        equipment_items: list[DocumentConfirmationItem] = []
        loop_items: list[DocumentConfirmationItem] = []
        interlock_items: list[DocumentConfirmationItem] = []
        sequence_items: list[DocumentConfirmationItem] = []
        alarm_items: list[DocumentConfirmationItem] = []

        updated_equipment = []
        for routine in model.equipment_routines:
            evidence = self._entity_evidence(entities, routine.equipment_tag)
            text_blob = "\n".join(evidence)
            has_behavior = self._any_pattern(
                text_blob,
                ["start", "stop", "run", "permissive", "fault", "manual", "auto", "open", "close"],
            )
            contradiction = self._any_pattern(text_blob, ["do not start", "never start", "must remain closed"])

            if contradiction:
                status = "CONTRADICTS_DOCUMENT"
                level = "CONFLICT"
                ref = "entity source snippets"
                note = "Document wording conflicts with inferred routine assumptions."
            elif has_behavior:
                status = "CONFIRMED_FROM_DOC"
                level = "CONFIRMED_FULL"
                ref = "entity source snippets"
                note = "Equipment behavior confirmed from extracted document snippets."
            elif any(
                row.get("target_entity", "").upper() == routine.equipment_tag.upper()
                or row.get("source_entity", "").upper() == routine.equipment_tag.upper()
                for row in relationship_rows
            ):
                status = "INFERRED_DEFAULT"
                level = "CONFIRMED_RELATIONSHIP"
                ref = "inferred_relationship metadata"
                note = "PARTIALLY CONFIRMED: Equipment tag and relationship context confirmed from document-derived graph edges; behavior scaffold inferred."
            else:
                status = "INFERRED_DEFAULT"
                level = "CONFIRMED_TAGS_ONLY" if evidence else "INFERRED_DEFAULT"
                ref = None
                note = (
                    "PARTIALLY CONFIRMED: Equipment tag present in extracted documents; behavior scaffold inferred."
                    if evidence
                    else "No explicit equipment behavior found in extracted documents."
                )

            updated_equipment.append(
                routine.model_copy(
                    update={
                        "confirmation_status": status,
                        "confirmation_level": level,
                        "source_reference": ref,
                        "confirmation_note": note,
                    }
                )
            )
            equipment_items.append(
                DocumentConfirmationItem(
                    element_id=routine.equipment_tag,
                    element_type="equipment",
                    status=status,
                    confirmation_level=level,
                    source_reference=ref,
                    message=note,
                    related_tags=[routine.equipment_tag],
                )
            )

        updated_loops = []
        for loop in model.loops:
            row = self._match_by_tags(loop_rows, [loop.sensor_tag, loop.actuator_tag], minimum_matches=2)
            fallback_row = self._match_by_tags(loop_rows, [loop.sensor_tag, loop.actuator_tag], minimum_matches=1)
            if row:
                status = "CONFIRMED_FROM_DOC"
                level = "CONFIRMED_FULL"
                ref = self._row_reference(row, "control_loop_definitions")
                note = "Loop pair and strategy references found in control narrative extraction."
                confirmed_loop_pairs.add((loop.sensor_tag.upper(), loop.actuator_tag.upper()))
            elif fallback_row:
                status = "INFERRED_DEFAULT"
                level = "CONFIRMED_RELATIONSHIP"
                ref = self._row_reference(fallback_row, "control_loop_definitions")
                note = "PARTIALLY CONFIRMED: Loop relationship found in extracted narrative; control strategy remains inferred."
            else:
                status = "INFERRED_DEFAULT"
                level = "INFERRED_DEFAULT"
                ref = None
                note = "No explicit PV/SP/actuator loop evidence found in extracted narrative."

            if fallback_row and "ratio" in str(fallback_row.get("source_sentence", "")).lower() and loop.control_strategy.upper() == "PID":
                status = "CONTRADICTS_DOCUMENT"
                level = "CONFLICT"
                ref = self._row_reference(fallback_row, "control_loop_definitions")
                note = "Narrative suggests ratio/cascade style control while generated strategy is PID."

            updated_loops.append(
                loop.model_copy(
                    update={
                        "confirmation_status": status,
                        "confirmation_level": level,
                        "source_reference": ref,
                        "confirmation_note": note,
                    }
                )
            )
            loop_items.append(
                DocumentConfirmationItem(
                    element_id=loop.loop_tag,
                    element_type="control_loop",
                    status=status,
                    confirmation_level=level,
                    source_reference=ref,
                    message=note,
                    related_tags=[loop.sensor_tag, loop.actuator_tag],
                )
            )

        updated_interlocks = []
        for interlock in model.interlocks:
            row = self._match_by_tags(interlock_rows, [interlock.source_tag, interlock.target_tag], minimum_matches=2)
            if row:
                status = "CONFIRMED_FROM_DOC"
                level = "CONFIRMED_FULL"
                ref = self._row_reference(row, "interlock_definitions")
                note = "Interlock linkage and trigger confirmed from extracted narrative."
            elif (
                (interlock.source_tag.upper(), interlock.target_tag.upper()) in confirmed_loop_pairs
                and bool(re.search(r"_HH_SP$|_HI_SP$", (interlock.threshold_tag or "").upper()))
            ):
                status = "INFERRED_DEFAULT"
                level = "CONFIRMED_CONTROL_LOOP_CONTEXT"
                ref = "control_loop + threshold pattern"
                note = "INFERRED PROTECTIVE INTERLOCK: generated from confirmed loop + HH/HI threshold pattern."
            else:
                status = "INFERRED_DEFAULT"
                level = "INFERRED_DEFAULT"
                ref = None
                note = "No explicit interlock statement found; generated protective interlock is inferred."

            updated_interlocks.append(
                interlock.model_copy(
                    update={
                        "confirmation_status": status,
                        "confirmation_level": level,
                        "source_reference": ref,
                        "confirmation_note": note,
                    }
                )
            )
            interlock_items.append(
                DocumentConfirmationItem(
                    element_id=interlock.interlock_id,
                    element_type="interlock",
                    status=status,
                    confirmation_level=level,
                    source_reference=ref,
                    message=note,
                    related_tags=[interlock.source_tag, interlock.target_tag],
                )
            )

        updated_alarms = []
        for group in model.alarm_groups:
            updated_rules = []
            for alarm in group.alarm_rules:
                row = self._match_by_tags(alarm_rows, [alarm.source_tag, alarm.alarm_tag], minimum_matches=1)
                if row:
                    status = "CONFIRMED_FROM_DOC"
                    level = "CONFIRMED_FULL"
                    ref = self._row_reference(row, "alarm_definitions")
                    note = "Alarm evidence found in extracted alarm/narrative definitions."
                elif (
                    any(pair[0] == alarm.source_tag.upper() for pair in confirmed_loop_pairs)
                    and alarm.alarm_type in {"HI", "HH", "LO", "LL"}
                ):
                    status = "INFERRED_DEFAULT"
                    level = "CONFIRMED_CONTROL_LOOP_CONTEXT"
                    ref = "control_loop threshold family context"
                    note = "PARTIALLY CONFIRMED: Alarm variable derived from document-supported threshold family context."
                else:
                    status = "INFERRED_DEFAULT"
                    level = "INFERRED_DEFAULT"
                    ref = None
                    note = "Alarm threshold/type is inferred from loop and equipment heuristics."

                updated_rules.append(
                    alarm.model_copy(
                        update={
                            "confirmation_status": status,
                            "confirmation_level": level,
                            "source_reference": ref,
                            "confirmation_note": note,
                        }
                    )
                )
                alarm_items.append(
                    DocumentConfirmationItem(
                        element_id=alarm.alarm_tag,
                        element_type="alarm",
                        status=status,
                        confirmation_level=level,
                        source_reference=ref,
                        message=note,
                        related_tags=[alarm.source_tag, alarm.alarm_tag],
                    )
                )
            updated_alarms.append(group.model_copy(update={"alarm_rules": updated_rules}))

        startup_evidence = []
        shutdown_evidence = []
        for entity in entities:
            for snippet in entity.source_snippets or []:
                lowered = snippet.lower()
                if "startup" in lowered or "start-up" in lowered:
                    startup_evidence.append(snippet)
                if "shutdown" in lowered or "shut-down" in lowered:
                    shutdown_evidence.append(snippet)

        def annotate_steps(steps, evidence, sequence_type: str):
            updated_steps = []
            for step in steps:
                if evidence:
                    status = "CONFIRMED_FROM_DOC"
                    level = "CONFIRMED_FULL"
                    ref = "entity source snippets"
                    note = f"{sequence_type.capitalize()} sequence evidence found in extracted procedure text."
                else:
                    status = "INFERRED_DEFAULT"
                    level = "INFERRED_DEFAULT"
                    ref = None
                    note = f"No explicit {sequence_type} procedure evidence found; deterministic scaffold retained."

                updated_steps.append(
                    step.model_copy(
                        update={
                            "confirmation_status": status,
                            "confirmation_level": level,
                            "source_reference": ref,
                            "confirmation_note": note,
                        }
                    )
                )
                sequence_items.append(
                    DocumentConfirmationItem(
                        element_id=f"{sequence_type}_{step.step_number}",
                        element_type="sequence",
                        status=status,
                        confirmation_level=level,
                        source_reference=ref,
                        message=note,
                        related_tags=[sequence_type, str(step.step_number)],
                    )
                )
            return updated_steps

        updated_startup = annotate_steps(model.startup_sequence, startup_evidence, "startup")
        updated_shutdown = annotate_steps(model.shutdown_sequence, shutdown_evidence, "shutdown")

        all_items = [*equipment_items, *loop_items, *interlock_items, *sequence_items, *alarm_items]
        if any(item.status == "CONTRADICTS_DOCUMENT" for item in all_items):
            overall = "conflict"
        elif all_items and all(item.status == "CONFIRMED_FROM_DOC" for item in all_items):
            overall = "confirmed"
        else:
            overall = "inferred"

        confirmation = DocumentConfirmationResult(
            project_id=project_id,
            equipment_logic=equipment_items,
            control_loops=loop_items,
            interlocks=interlock_items,
            sequences=sequence_items,
            alarms=alarm_items,
            confirmation_status=overall,
        )

        updated_model = model.model_copy(
            update={
                "equipment_routines": updated_equipment,
                "loops": updated_loops,
                "interlocks": updated_interlocks,
                "alarm_groups": updated_alarms,
                "startup_sequence": updated_startup,
                "shutdown_sequence": updated_shutdown,
            }
        )

        self.logger.info(
            "Document confirmation completed: project=%s status=%s equipment=%s loops=%s interlocks=%s sequences=%s alarms=%s",
            project_id,
            overall,
            len(equipment_items),
            len(loop_items),
            len(interlock_items),
            len(sequence_items),
            len(alarm_items),
        )
        return updated_model, confirmation


document_confirmation_engine = DocumentConfirmationEngine()
