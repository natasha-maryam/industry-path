from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from psycopg2.extras import Json

from db.postgres import postgres_client
from models.logic import (
    ControlRule,
    GeneratedSTFile,
    LogicGenerationResult,
    RejectedRuleCandidate,
    STGenerationResult,
)
from models.generation import GenerationReport, GeneratedLogicFile, IOMappingEntry, ValidationIssue as GenerationValidationIssue
from models.pipeline import EngineeringEntity
from services.control_loop_engine import control_loop_engine
from services.control_rule_candidate_service import control_rule_candidate_service
from services.control_rule_extraction_service import ExtractedRuleDraft, control_rule_extraction_service
from services.control_rule_normalization_service import control_rule_normalization_service
from services.graph_service import graph_service
from services.engineering_validator import engineering_validator
from services.io_mapping_engine import io_mapping_engine
from services.logic_completion_engine import logic_completion_engine
from services.document_confirmation_engine import document_confirmation_engine
from services.narrative_segmentation_service import narrative_segmentation_service
from services.project_service import project_service
from services.runtime_deployer import runtime_deployer
from services.st_generator import st_generator
from services.st_renderer_service import st_renderer_service
from services.st_validator import st_validator
from services.version_manager import version_manager
from services.virtual_commissioning import virtual_commissioning_service


class ControlLogicService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.generator_version = "deterministic-v3"

    @staticmethod
    def _resolve_file_path(relative_file_path: str) -> Path:
        workspace_root = Path(__file__).resolve().parents[2]
        return (workspace_root / relative_file_path).resolve()

    def _load_narrative_files(self, project_id: str) -> list[dict]:
        return postgres_client.fetch_all(
            """
            SELECT id::text AS id,
                   original_name,
                   file_path,
                   document_type,
                   uploaded_at
            FROM project_files
            WHERE project_id = %s
              AND document_type = 'control_narrative'
            ORDER BY uploaded_at ASC
            """,
            (project_id,),
        )

    def _load_entity_index(self, project_id: str) -> dict[str, dict]:
        rows = postgres_client.fetch_all(
            """
            SELECT em.payload AS payload
            FROM extracted_metadata em
            JOIN (
                SELECT project_id, MAX(started_at) AS max_started
                FROM parse_batches
                WHERE project_id = %s
                GROUP BY project_id
            ) latest ON latest.project_id = em.project_id
            JOIN parse_batches pb ON pb.project_id = em.project_id
                                 AND pb.id = em.parse_batch_id
                                 AND pb.started_at = latest.max_started
            WHERE em.project_id = %s
              AND em.category = 'engineering_entity'
            ORDER BY em.created_at ASC
            """,
            (project_id, project_id),
        )

        index: dict[str, dict] = {}
        for row in rows:
            payload = row.get("payload") or {}
            entity_id = payload.get("id")
            if not entity_id:
                continue

            entity_id = str(entity_id).upper()
            aliases = payload.get("aliases") or []
            aliases = [str(alias).upper().replace("_", "-") for alias in aliases]
            aliases.append(entity_id)

            index[entity_id] = {
                "id": entity_id,
                "canonical_type": payload.get("canonical_type", "generic_device"),
                "display_name": payload.get("display_name") or entity_id,
                "aliases": aliases,
                "process_unit": payload.get("process_unit"),
            }

        if index:
            return index

        graph = graph_service.get_graph(project_id)
        for node in graph.nodes:
            node_id = node.id.upper()
            index[node_id] = {
                "id": node_id,
                "canonical_type": node.node_type,
                "display_name": node.label,
                "aliases": [node_id, node.label.upper().replace(" ", "-")],
                "process_unit": node.process_unit,
            }

        return index

    @staticmethod
    def _rule_sort_key(rule: ControlRule) -> tuple[int, float]:
        return rule.priority, -rule.confidence

    def _group_by_unit(self, entity_index: dict[str, dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for entity in entity_index.values():
            unit = str(entity.get("process_unit") or "").lower()
            grouped.setdefault(unit, []).append(entity)
        return grouped

    @staticmethod
    def _match_unit_for_group(group: str, unit_key: str) -> bool:
        mapping = {
            "influent_pump_station": ("influent", "pump_station", "wet_well"),
            "screening": ("screen",),
            "grit_removal": ("grit",),
            "aeration": ("aeration",),
            "blower_package": ("blower", "air_header"),
            "chemical_feed": ("chemical",),
            "clarifier": ("clarifier", "sludge"),
        }
        tokens = mapping.get(group, ())
        return any(token in unit_key for token in tokens)

    def _find_entity(
        self,
        entity_index: dict[str, dict],
        *,
        canonical_types: set[str] | None = None,
        group: str | None = None,
        preferred_names: tuple[str, ...] = (),
    ) -> dict | None:
        canonical_types = canonical_types or set()
        items = list(entity_index.values())

        if group:
            grouped = self._group_by_unit(entity_index)
            candidate_units = [key for key in grouped if self._match_unit_for_group(group, key)]
            if candidate_units:
                items = [entry for key in candidate_units for entry in grouped[key]]

        for name in preferred_names:
            low = name.lower()
            for entry in items:
                if canonical_types and entry.get("canonical_type") not in canonical_types:
                    continue
                display = str(entry.get("display_name") or "").lower()
                aliases = " ".join(str(alias).lower() for alias in entry.get("aliases", []))
                if low in display or low in aliases:
                    return entry

        for entry in items:
            if canonical_types and entry.get("canonical_type") not in canonical_types:
                continue
            return entry

        return None

    def _find_entity_with_priority(
        self,
        entity_index: dict[str, dict],
        *,
        canonical_types: set[str] | None = None,
        group: str | None = None,
        explicit_tags: tuple[str, ...] = (),
        preferred_names: tuple[str, ...] = (),
    ) -> tuple[dict | None, str]:
        canonical_types = canonical_types or set()

        for raw in explicit_tags:
            key = raw.upper().replace("_", "-")
            entry = entity_index.get(key)
            if not entry:
                continue
            if canonical_types and entry.get("canonical_type") not in canonical_types:
                continue
            return entry, "exact_tag"

        by_name = self._find_entity(
            entity_index,
            canonical_types=canonical_types,
            group=group,
            preferred_names=preferred_names,
        )
        if by_name is not None:
            return by_name, "alias_match"

        by_group = self._find_entity(entity_index, canonical_types=canonical_types, group=group)
        if by_group is not None:
            return by_group, "unit_match"

        return None, "synthetic_placeholder"

    def _section_templates(self, entity_index: dict[str, dict], sentences: list[str]) -> list[ExtractedRuleDraft]:
        corpus = "\n".join(sentences).lower()
        rules: list[ExtractedRuleDraft] = []

        def add_rule(**kwargs) -> None:
            rules.append(ExtractedRuleDraft(**kwargs))

        lit, lit_strategy = self._find_entity_with_priority(
            entity_index,
            canonical_types={"level_transmitter", "level_switch"},
            group="influent_pump_station",
            explicit_tags=("LIT-2001",),
            preferred_names=("lit-2001", "wet well", "wet well level"),
        )
        lshh, lshh_strategy = self._find_entity_with_priority(
            entity_index,
            canonical_types={"level_switch", "level_transmitter"},
            group="influent_pump_station",
            explicit_tags=("LSHH-2001",),
            preferred_names=("high-high", "lshh", "wet well high"),
        )
        lead_pump, lead_strategy = self._find_entity_with_priority(
            entity_index,
            canonical_types={"pump"},
            group="influent_pump_station",
            explicit_tags=("PMP-2001",),
            preferred_names=("lead", "duty", "influent pump", "pmp-2001"),
        )
        lag_pump, lag_strategy = self._find_entity_with_priority(
            entity_index,
            canonical_types={"pump"},
            group="influent_pump_station",
            explicit_tags=("PMP-2002",),
            preferred_names=("lag", "standby", "pmp-2002"),
        )
        if lag_pump is None:
            lag_pump = lead_pump
            lag_strategy = lead_strategy

        if lit and lead_pump and ("influent" in corpus or "wet well" in corpus):
            add_rule(
                rule_group="influent_pump_station",
                rule_type="start_stop",
                source_tag=lit["id"],
                source_type=lit["canonical_type"],
                condition_kind="level",
                operator="<=",
                threshold="LOW_LEVEL",
                threshold_name="LOW_LEVEL",
                action="STOP",
                target_tag=lead_pump["id"],
                target_type=lead_pump["canonical_type"],
                secondary_target_tag=lag_pump["id"] if lag_pump else None,
                mode="AUTO",
                priority=10,
                confidence=0.92,
                source_sentence="Low level in wet well stops pumps.",
                source_page=None,
                section_heading="influent_pump_station",
                explanation="Template: low level stop for influent pumps.",
                resolution_strategy=lit_strategy,
                renderable=True,
                unresolved_tokens=[],
                comments=[],
                source_references=["template:influent_low_level_stop"],
            )
            add_rule(
                rule_group="influent_pump_station",
                rule_type="start_stop",
                source_tag=lit["id"],
                source_type=lit["canonical_type"],
                condition_kind="level",
                operator=">=",
                threshold="NORMAL_LEVEL",
                threshold_name="NORMAL_LEVEL",
                action="START",
                target_tag=lead_pump["id"],
                target_type=lead_pump["canonical_type"],
                secondary_target_tag=None,
                mode="AUTO",
                priority=11,
                confidence=0.91,
                source_sentence="Normal wet well level starts lead pump.",
                source_page=None,
                section_heading="influent_pump_station",
                explanation="Template: normal level lead pump start.",
                resolution_strategy=lead_strategy,
                renderable=True,
                unresolved_tokens=[],
                comments=[],
                source_references=["template:influent_normal_level_lead_start"],
            )
            add_rule(
                rule_group="influent_pump_station",
                rule_type="start_stop",
                source_tag=lit["id"],
                source_type=lit["canonical_type"],
                condition_kind="level",
                operator=">=",
                threshold="HIGH_LEVEL",
                threshold_name="HIGH_LEVEL",
                action="START",
                target_tag=lag_pump["id"] if lag_pump else lead_pump["id"],
                target_type=(lag_pump or lead_pump)["canonical_type"],
                secondary_target_tag=lead_pump["id"],
                mode="AUTO",
                priority=11,
                confidence=0.9,
                source_sentence="High level in wet well starts lag pump.",
                source_page=None,
                section_heading="influent_pump_station",
                explanation="Template: high level lag pump start.",
                resolution_strategy=lag_strategy,
                renderable=True,
                unresolved_tokens=[],
                comments=["lead/lag rotation schedule inferred; exact timer not parsed."],
                source_references=["template:influent_high_level_start"],
            )
            hh_source = lshh or lit
            hh_source_type = (lshh or lit)["canonical_type"]
            add_rule(
                rule_group="influent_pump_station",
                rule_type="alarm",
                source_tag=hh_source["id"],
                source_type=hh_source_type,
                condition_kind="level",
                operator=">=",
                threshold="HIGH_HIGH_LEVEL",
                threshold_name="HIGH_HIGH_LEVEL",
                action="ALARM",
                target_tag="WET_WELL_HIGH_HIGH",
                target_type="process_unit",
                secondary_target_tag=None,
                mode="AUTO",
                priority=12,
                confidence=0.88,
                source_sentence="High-high wet well level alarm.",
                source_page=None,
                section_heading="influent_pump_station",
                explanation="Template: wet well high-high alarm.",
                resolution_strategy=lshh_strategy if lshh else lit_strategy,
                renderable=True,
                unresolved_tokens=[] if lshh else ["symbolic_alarm_target"],
                comments=(
                    [f"__HH_START_PUMPS__:{lead_pump['id']},{lag_pump['id']}"]
                    + ([] if lshh else ["using symbolic alarm target until explicit alarm tag mapping is parsed."])
                ),
                source_references=["template:influent_hh_alarm"],
            )
            add_rule(
                rule_group="influent_pump_station",
                rule_type="interlock",
                source_tag=lit["id"],
                source_type=lit["canonical_type"],
                condition_kind="level",
                operator="<=",
                threshold="LOW_LOW",
                threshold_name="LOW_LOW",
                action="DISABLE",
                target_tag=lead_pump["id"],
                target_type=lead_pump["canonical_type"],
                secondary_target_tag=lag_pump["id"] if lag_pump else None,
                mode="AUTO",
                priority=14,
                confidence=0.84,
                source_sentence="Low-low wet well level interlock.",
                source_page=None,
                section_heading="influent_pump_station",
                explanation="Template: low-low interlock stops and inhibits pumps.",
                resolution_strategy=lit_strategy,
                renderable=True,
                unresolved_tokens=[],
                comments=["minimum level permissive interlock inferred from narrative."],
                source_references=["template:influent_low_low_interlock"],
            )
            add_rule(
                rule_group="influent_pump_station",
                rule_type="lead_lag",
                source_tag=lit["id"],
                source_type=lit["canonical_type"],
                condition_kind="timer",
                operator="timer_elapsed",
                threshold="ROTATION_INTERVAL",
                threshold_name="ROTATION_INTERVAL",
                action="SWITCH_TO_LEAD",
                target_tag=lead_pump["id"],
                target_type=lead_pump["canonical_type"],
                secondary_target_tag=lag_pump["id"] if lag_pump else None,
                mode="AUTO",
                priority=15,
                confidence=0.76,
                source_sentence="Lead/lag pump rotation.",
                source_page=None,
                section_heading="influent_pump_station",
                explanation="Template: lead/lag rotation placeholder.",
                resolution_strategy="unit_match",
                renderable=True,
                unresolved_tokens=["rotation_timer"],
                comments=["TODO: exact lead/lag rotation timer not parsed from narrative."],
                source_references=["template:influent_rotation_placeholder"],
            )

        if "screen" in corpus or "differential pressure" in corpus:
            dpit = self._find_entity(entity_index, canonical_types={"differential_pressure_transmitter"}, group="screening", preferred_names=("dpit", "differential pressure"))
            screen = self._find_entity(entity_index, canonical_types={"process_unit", "generic_device"}, group="screening", preferred_names=("screen",))
            dpit_id = dpit["id"] if dpit else "DPIT_2101"
            dpit_type = dpit["canonical_type"] if dpit else "differential_pressure_transmitter"
            screen_id = screen["id"] if screen else "SCREENING_UNIT"
            screen_type = screen["canonical_type"] if screen else "process_unit"
            add_rule(
                rule_group="screening",
                rule_type="start_stop",
                source_tag=dpit_id,
                source_type=dpit_type,
                condition_kind="differential_pressure",
                operator=">=",
                threshold="DP_SETPOINT",
                threshold_name="DP_SETPOINT",
                action="START",
                target_tag=screen_id,
                target_type=screen_type,
                secondary_target_tag=None,
                mode="AUTO",
                priority=12,
                confidence=0.88,
                source_sentence="High differential pressure starts screen.",
                source_page=None,
                section_heading="screening",
                explanation="Template: screening start on high differential pressure.",
                renderable=True,
                unresolved_tokens=[] if dpit and screen else ["template_placeholder"],
                comments=["using symbolic DP_SETPOINT until exact reset threshold is parsed."],
                source_references=["template:screening_dp_start"],
            )
            add_rule(
                rule_group="screening",
                rule_type="alarm",
                source_tag=dpit_id,
                source_type=dpit_type,
                condition_kind="differential_pressure",
                operator=">=",
                threshold="HIGH_DP",
                threshold_name="HIGH_DP",
                action="ALARM",
                target_tag="SCREEN_HIGH_DP_ALARM",
                target_type="process_unit",
                secondary_target_tag=None,
                mode="AUTO",
                priority=13,
                confidence=0.84,
                source_sentence="High differential pressure alarm on screening unit.",
                source_page=None,
                section_heading="screening",
                explanation="Template: screening high DP alarm.",
                renderable=True,
                unresolved_tokens=[] if dpit else ["template_placeholder"],
                comments=[],
                source_references=["template:screening_high_dp_alarm"],
            )

        ait = self._find_entity(entity_index, canonical_types={"analyzer"}, group="aeration", preferred_names=("ait", "do analyzer"))
        fcv = self._find_entity(entity_index, canonical_types={"control_valve", "valve"}, group="aeration", preferred_names=("fcv", "air valve"))
        if ait and fcv and ("aeration" in corpus or "dissolved oxygen" in corpus or "do" in corpus):
            add_rule(
                rule_group="aeration",
                rule_type="pid_loop",
                source_tag=ait["id"],
                source_type=ait["canonical_type"],
                condition_kind="analyzer",
                operator="<",
                threshold="DO_SETPOINT",
                threshold_name="DO_SETPOINT",
                action="MODULATE",
                target_tag=fcv["id"],
                target_type=fcv["canonical_type"],
                secondary_target_tag=None,
                mode="AUTO",
                priority=13,
                confidence=0.93,
                source_sentence="DO analyzer controls air valve.",
                source_page=None,
                section_heading="aeration",
                explanation="Template: analyzer-driven control valve modulation.",
                renderable=True,
                unresolved_tokens=[],
                comments=["exact PID coefficients and deadband not parsed."],
                source_references=["template:aeration_do_pid"],
            )
            add_rule(
                rule_group="aeration",
                rule_type="alarm",
                source_tag=ait["id"],
                source_type=ait["canonical_type"],
                condition_kind="analyzer",
                operator="<",
                threshold="LOW_DO_LIMIT",
                threshold_name="LOW_DO_LIMIT",
                action="ALARM",
                target_tag="LOW_DO_ALARM",
                target_type="process_unit",
                secondary_target_tag=None,
                mode="AUTO",
                priority=14,
                confidence=0.86,
                source_sentence="Low dissolved oxygen alarm.",
                source_page=None,
                section_heading="aeration",
                explanation="Template: low DO alarm.",
                renderable=True,
                unresolved_tokens=[],
                comments=[],
                source_references=["template:aeration_low_do_alarm"],
            )

        if "blower" in corpus or "header pressure" in corpus:
            pit, pit_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"pressure_transmitter"},
                group="blower_package",
                explicit_tags=("PIT-4001",),
                preferred_names=("pit-4001", "header pressure"),
            )
            blower, blower_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"blower"},
                group="blower_package",
                explicit_tags=("BL-4002", "BL-4001"),
                preferred_names=("standby", "lag", "blower"),
            )
            pit_id = pit["id"] if pit else "PIT_4001"
            pit_type = pit["canonical_type"] if pit else "pressure_transmitter"
            blower_id = blower["id"] if blower else "STANDBY_BLOWER"
            blower_type = blower["canonical_type"] if blower else "blower"
            add_rule(
                rule_group="blower_package",
                rule_type="start_stop",
                source_tag=pit_id,
                source_type=pit_type,
                condition_kind="pressure",
                operator="<",
                threshold="HEADER_PRESSURE_LOW",
                threshold_name="HEADER_PRESSURE_LOW",
                action="START",
                target_tag=blower_id,
                target_type=blower_type,
                secondary_target_tag=None,
                mode="AUTO",
                priority=14,
                confidence=0.89,
                source_sentence="Low header pressure starts standby blower.",
                source_page=None,
                section_heading="blower_package",
                explanation="Template: pressure-based blower staging.",
                resolution_strategy=blower_strategy if blower else "synthetic_placeholder",
                renderable=True,
                unresolved_tokens=[] if pit and blower else ["template_placeholder"],
                comments=["exact standby blower selection logic unresolved; using first blower candidate."],
                source_references=["template:blower_pressure_stage"],
            )
            add_rule(
                rule_group="blower_package",
                rule_type="start_stop",
                source_tag=pit_id,
                source_type=pit_type,
                condition_kind="pressure",
                operator=">",
                threshold="HEADER_PRESSURE_HIGH",
                threshold_name="HEADER_PRESSURE_HIGH",
                action="STOP",
                target_tag=blower["id"] if blower else "LAG_BLOWER",
                target_type=blower_type,
                secondary_target_tag=None,
                mode="AUTO",
                priority=15,
                confidence=0.84,
                source_sentence="High header pressure stops lag blower.",
                source_page=None,
                section_heading="blower_package",
                explanation="Template: high pressure lag blower stop.",
                resolution_strategy=blower_strategy if blower else "synthetic_placeholder",
                renderable=True,
                unresolved_tokens=[] if blower else ["lag_blower_assignment"],
                comments=[] if blower else ["lag/standby blower assignment unresolved; symbolic LAG_BLOWER retained."],
                source_references=["template:blower_high_pressure_stop"],
            )

        if "grit" in corpus:
            grit_level = self._find_entity(entity_index, canonical_types={"level_transmitter", "level_switch"}, group="grit_removal", preferred_names=("lit", "grit level"))
            grit_pump = self._find_entity(entity_index, canonical_types={"pump", "generic_device", "process_unit"}, group="grit_removal", preferred_names=("grit pump", "classifier"))
            add_rule(
                rule_group="grit_removal",
                rule_type="start_stop",
                source_tag=(grit_level or {}).get("id", "LIT_2201"),
                source_type=(grit_level or {}).get("canonical_type", "level_transmitter"),
                condition_kind="level",
                operator=">=",
                threshold="GRIT_HIGH",
                threshold_name="GRIT_HIGH",
                action="START",
                target_tag=(grit_pump or {}).get("id", "PMP_2201"),
                target_type=(grit_pump or {}).get("canonical_type", "pump"),
                secondary_target_tag=None,
                mode="AUTO",
                priority=15,
                confidence=0.86,
                source_sentence="High grit chamber level starts grit removal pump.",
                source_page=None,
                section_heading="grit_removal",
                explanation="Template: grit chamber high level start.",
                renderable=True,
                unresolved_tokens=[] if grit_level and grit_pump else ["template_placeholder"],
                comments=["symbolic grit threshold retained until numeric value is parsed."],
                source_references=["template:grit_high_level_start"],
            )

        if "chemical" in corpus or "dosing" in corpus or "polymer" in corpus:
            fit, fit_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"flow_transmitter"},
                group="chemical_feed",
                explicit_tags=("FIT-4501",),
                preferred_names=("fit-4501", "chemical flow", "influent flow"),
            )
            chem_pump, pump_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"pump", "chemical_system_device"},
                group="chemical_feed",
                explicit_tags=("PMP-4501", "PMP-4502"),
                preferred_names=("polymer", "coagulant", "chemical", "dosing", "pmp-4501", "pmp-4502"),
            )
            add_rule(
                rule_group="chemical_feed",
                rule_type="ratio_control",
                source_tag=(fit or {}).get("id", "FIT_4501"),
                source_type=(fit or {}).get("canonical_type", "flow_transmitter"),
                condition_kind="flow",
                operator=">=",
                threshold="FLOW_SETPOINT",
                threshold_name="FLOW_SETPOINT",
                action="MODULATE",
                target_tag=(chem_pump or {}).get("id", "PMP_4501"),
                target_type=(chem_pump or {}).get("canonical_type", "pump"),
                secondary_target_tag=None,
                mode="AUTO",
                priority=16,
                confidence=0.87,
                source_sentence="Chemical dosing is proportional to influent flow.",
                source_page=None,
                section_heading="chemical_feed",
                explanation="Template: flow-paced chemical dosing.",
                resolution_strategy=pump_strategy if chem_pump else fit_strategy,
                renderable=True,
                unresolved_tokens=[] if fit and chem_pump else ["template_placeholder"],
                comments=["ratio constant unresolved; FLOW_SETPOINT acts as symbolic pacing reference."],
                source_references=["template:chemical_flow_ratio"],
            )

        if "clarifier" in corpus or "sludge" in corpus or "blanket" in corpus:
            blanket, blanket_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"level_transmitter", "analyzer", "level_switch"},
                group="clarifier",
                explicit_tags=("LIT-2601",),
                preferred_names=("lit-2601", "blanket", "clarifier level"),
            )
            sludge_pump, sludge_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"pump"},
                group="clarifier",
                explicit_tags=("PMP-2601", "PMP-2602"),
                preferred_names=("sludge", "was", "ras", "pmp-2601", "pmp-2602"),
            )
            add_rule(
                rule_group="clarifier",
                rule_type="start_stop",
                source_tag=(blanket or {}).get("id", "LIT_2601"),
                source_type=(blanket or {}).get("canonical_type", "level_transmitter"),
                condition_kind="level",
                operator=">=",
                threshold="BLANKET_HIGH",
                threshold_name="BLANKET_HIGH",
                action="START",
                target_tag=(sludge_pump or {}).get("id", "PMP_2601"),
                target_type=(sludge_pump or {}).get("canonical_type", "pump"),
                secondary_target_tag=None,
                mode="AUTO",
                priority=17,
                confidence=0.85,
                source_sentence="High sludge blanket starts sludge withdrawal pump.",
                source_page=None,
                section_heading="clarifier",
                explanation="Template: clarifier blanket control.",
                resolution_strategy=sludge_strategy if sludge_pump else blanket_strategy,
                renderable=True,
                unresolved_tokens=[] if blanket and sludge_pump else ["template_placeholder"],
                comments=["blanket control deadband unresolved."],
                source_references=["template:clarifier_blanket_start"],
            )

        if "startup" in corpus or "shutdown" in corpus or "emergency" in corpus or any(
            token in corpus for token in ("auto", "manual", "override", "local", "remote")
        ):
            startup_target, startup_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"process_unit", "generic_device"},
                preferred_names=("headworks", "process", "train", "plant"),
            )
            permissive_source, permissive_strategy = self._find_entity_with_priority(
                entity_index,
                canonical_types={"level_switch", "level_transmitter", "pressure_transmitter", "generic_device"},
                group="influent_pump_station",
                preferred_names=("permissive", "lit", "pit", "switch"),
            )
            add_rule(
                rule_group="startup_shutdown",
                rule_type="sequence",
                source_tag=(permissive_source or {}).get("id", "STARTUP_PERMISSIVE"),
                source_type=(permissive_source or {}).get("canonical_type", "generic_device"),
                condition_kind="boolean_state",
                operator="==",
                threshold="STARTUP_PERMISSIVE",
                threshold_name="STARTUP_PERMISSIVE",
                action="ENABLE",
                target_tag=(startup_target or {}).get("id", "HEADWORKS_PROCESS"),
                target_type=(startup_target or {}).get("canonical_type", "process_unit"),
                secondary_target_tag=None,
                mode="AUTO",
                priority=18,
                confidence=0.82,
                source_sentence="Startup permissive enables process train.",
                source_page=None,
                section_heading="startup_shutdown",
                explanation="Template: startup permissive sequence.",
                resolution_strategy=permissive_strategy if permissive_source else startup_strategy,
                renderable=True,
                unresolved_tokens=[] if startup_target else ["template_placeholder"],
                comments=["startup step sequencing order remains symbolic."],
                source_references=["template:startup_permissive_enable"],
            )
            add_rule(
                rule_group="modes",
                rule_type="mode",
                source_tag=(startup_target or {}).get("id", "MODE_SELECTOR"),
                source_type="generic_device",
                condition_kind="mode",
                operator="manual_command",
                threshold="AUTO_MANUAL",
                threshold_name="AUTO_MANUAL",
                action="ENABLE",
                target_tag=(startup_target or {}).get("id", "PROCESS_TRAIN"),
                target_type=(startup_target or {}).get("canonical_type", "process_unit"),
                secondary_target_tag=None,
                mode="AUTO",
                priority=19,
                confidence=0.68,
                source_sentence="Manual override and AUTO/MANUAL handling inferred from narrative.",
                source_page=None,
                section_heading="modes",
                explanation="Template: mode/override placeholder section.",
                resolution_strategy=startup_strategy,
                renderable=True,
                unresolved_tokens=["manual_override_logic"],
                comments=["TODO: Manual override and AUTO/MANUAL mode handling inferred from narrative."],
                source_references=["template:modes_override_placeholder"],
            )

        return rules

    def _enrich_with_graph_context(self, project_id: str, rules: list[ControlRule], entity_index: dict[str, dict]) -> tuple[list[ControlRule], list[str]]:
        graph = graph_service.get_graph(project_id)
        node_ids = {node.id.upper() for node in graph.nodes}
        warnings: list[str] = []

        source_type_map = {
            "level": {"level_transmitter", "level_switch"},
            "pressure": {"pressure_transmitter"},
            "differential_pressure": {"differential_pressure_transmitter"},
            "analyzer": {"analyzer"},
            "flow": {"flow_transmitter"},
        }
        target_type_map = {
            "START": {"pump", "blower", "generic_device", "process_unit"},
            "STOP": {"pump", "blower", "generic_device", "process_unit"},
            "OPEN": {"control_valve", "valve"},
            "CLOSE": {"control_valve", "valve"},
            "MODULATE": {"control_valve", "valve", "pump", "chemical_system_device"},
            "ALARM": {"process_unit", "generic_device", "alarm", "analyzer"},
            "ENABLE": {"process_unit", "generic_device", "pump", "blower"},
            "DISABLE": {"process_unit", "generic_device", "pump", "blower", "control_valve"},
        }

        group_hints = {
            "chemical_feed": {
                "source": ("fit-4501", "flow", "chemical flow"),
                "target": ("pmp-4501", "pmp-4502", "chemical pump", "polymer"),
            },
            "clarifier": {
                "source": ("lit-2601", "cl-2601", "blanket", "clarifier"),
                "target": ("pmp-2601", "pmp-2602", "sludge pump", "ras", "was"),
            },
            "influent_pump_station": {
                "source": ("lit-2001", "lshh-2001", "wet well"),
                "target": ("pmp-2001", "pmp-2002", "influent"),
            },
            "blower_package": {
                "source": ("pit-4001", "header pressure"),
                "target": ("bl-4001", "bl-4002", "standby", "lag blower"),
            },
        }

        def canonical_for_source(rule: ControlRule) -> set[str]:
            mapped = source_type_map.get(rule.condition_kind or "", set())
            if mapped:
                return mapped
            if rule.source_type:
                return {rule.source_type}
            return set()

        def canonical_for_target(rule: ControlRule) -> set[str]:
            mapped = target_type_map.get(rule.action, set())
            if mapped:
                return mapped
            if rule.target_type:
                return {rule.target_type}
            return set()

        def is_template_symbolic(tag: str | None, rule: ControlRule) -> bool:
            if not tag:
                return False
            if not any(ref.startswith("template:") for ref in rule.source_references):
                return False
            return tag.startswith(
                (
                    "DPIT_",
                    "PIT_",
                    "LS",
                    "LIT_",
                    "FIT_",
                    "PMP_",
                    "SCREEN_",
                    "LOW_",
                    "HIGH_",
                    "STANDBY_",
                    "STARTUP_",
                    "HEADWORKS_",
                )
            )

        for rule in rules:
            if rule.source_tag and rule.source_tag.upper() not in node_ids and rule.source_tag.upper() not in entity_index:
                replacement = self._find_entity(
                    entity_index,
                    canonical_types=canonical_for_source(rule),
                    group=rule.rule_group,
                    preferred_names=group_hints.get(rule.rule_group, {}).get("source", ()),
                )
                if replacement:
                    warnings.append(
                        f"Rule {rule.id}: replaced symbolic source tag {rule.source_tag} with parsed tag {replacement['id']}"
                    )
                    rule.source_tag = replacement["id"]
                    rule.source_type = replacement.get("canonical_type")
                    rule.resolution_strategy = "unit_match"
                elif is_template_symbolic(rule.source_tag, rule):
                    rule.comments.append(f"symbolic source tag retained: {rule.source_tag}")
                    warnings.append(f"Rule {rule.id}: symbolic source placeholder used ({rule.source_tag})")
                else:
                    warnings.append(f"Rule {rule.id}: source tag not found in graph/entities ({rule.source_tag})")
                    rule.confidence = max(0.2, rule.confidence - 0.12)
                    rule.renderable = False
                    rule.resolution_strategy = "synthetic_placeholder"

            if rule.target_tag and rule.target_tag.upper() not in node_ids and rule.target_tag.upper() not in entity_index:
                replacement = self._find_entity(
                    entity_index,
                    canonical_types=canonical_for_target(rule),
                    group=rule.rule_group,
                    preferred_names=group_hints.get(rule.rule_group, {}).get("target", ()),
                )
                if replacement:
                    warnings.append(
                        f"Rule {rule.id}: replaced symbolic target tag {rule.target_tag} with parsed tag {replacement['id']}"
                    )
                    rule.target_tag = replacement["id"]
                    rule.target_type = replacement.get("canonical_type")
                    if rule.resolution_strategy in {"synthetic_placeholder", "alias_match"}:
                        rule.resolution_strategy = "unit_match"
                elif is_template_symbolic(rule.target_tag, rule):
                    rule.comments.append(f"symbolic target tag retained: {rule.target_tag}")
                    warnings.append(f"Rule {rule.id}: symbolic target placeholder used ({rule.target_tag})")
                else:
                    warnings.append(f"Rule {rule.id}: target tag not found in graph/entities ({rule.target_tag})")
                    rule.confidence = max(0.2, rule.confidence - 0.12)
                    rule.renderable = False
                    rule.resolution_strategy = "synthetic_placeholder"

            if rule.source_type == "process_unit":
                warnings.append(f"Rule {rule.id}: process unit used as condition source; forcing non-renderable TODO")
                rule.comments.append("Replace process unit condition with sensor trigger before deployment.")
                rule.renderable = False

        return rules, warnings

    @staticmethod
    def _reject(rule: ControlRule) -> str | None:
        if not rule.renderable:
            return "rule marked non-renderable"
        if rule.source_type == "process_unit":
            return "process unit cannot be used as boolean condition"
        if "IF TRUE" in rule.st_preview.upper():
            return "invalid unconditional IF TRUE"
        if "TODO_CONDITION" in rule.display_text:
            return "condition unresolved"
        if "TODO_TARGET" in rule.display_text:
            return "target unresolved"
        if rule.action in {"START", "STOP", "OPEN", "CLOSE", "MODULATE", "DISABLE"} and not rule.target_tag:
            return "target unresolved for actionable command"
        if rule.rule_type == "alarm" and not rule.source_tag:
            return "alarm trigger unresolved"
        if rule.rule_type in {"mode", "sequence"} and not rule.source_tag:
            return "mode/sequence rule missing concrete trigger"
        if rule.rule_type in {"mode", "sequence"} and rule.confidence < 0.85:
            return "mode/startup rule too vague; rendered as TODO placeholder"
        if rule.rule_type in {"mode", "sequence"} and (
            (rule.source_tag or "").startswith("STARTUP_")
            or (rule.source_tag or "").endswith("_STATE")
        ):
            return "mode/startup rule is symbolic and not executable"
        if rule.is_symbolic and rule.target_type == "process_unit" and rule.action in {"ENABLE", "DISABLE", "START", "STOP"}:
            return "symbolic process-unit action retained as section TODO"
        if (
            rule.rule_type == "lead_lag"
            and rule.condition_kind == "boolean_state"
            and not (rule.operator and (rule.threshold_name or rule.threshold))
        ):
            return "lead/lag trigger too weak; requires explicit runtime/pressure/fault condition"
        return None

    @staticmethod
    def _is_symbolic_rule(rule: ControlRule) -> bool:
        if rule.resolution_strategy == "synthetic_placeholder":
            return True
        if rule.unresolved_tokens:
            return True
        if any("symbolic" in item.lower() or "placeholder" in item.lower() for item in rule.comments):
            return True
        return False

    @staticmethod
    def _split_rendered_rules(rules: list[ControlRule]) -> tuple[list[ControlRule], list[ControlRule]]:
        final_rendered = [rule for rule in rules if not rule.is_symbolic]
        symbolic_rendered = [rule for rule in rules if rule.is_symbolic]
        return final_rendered, symbolic_rendered

    def _promote_warning_rules(
        self,
        entity_index: dict[str, dict],
        warnings: list[str],
    ) -> tuple[list[ExtractedRuleDraft], list[str]]:
        promoted: list[ExtractedRuleDraft] = []
        leftovers: list[str] = []

        for warning in warnings:
            lowered = warning.lower()
            handled = False

            if "wet well high-high" in lowered or "high-high level switch" in lowered:
                source, strategy = self._find_entity_with_priority(
                    entity_index,
                    canonical_types={"level_switch", "level_transmitter"},
                    group="influent_pump_station",
                    explicit_tags=("LSHH-2001", "LIT-2001"),
                    preferred_names=("wet well", "high-high", "lshh"),
                )
                if source:
                    promoted.append(
                        ExtractedRuleDraft(
                            rule_group="influent_pump_station",
                            rule_type="alarm",
                            source_tag=source["id"],
                            source_type=source["canonical_type"],
                            condition_kind="level",
                            operator=">=",
                            threshold="HIGH_HIGH_LEVEL",
                            threshold_name="HIGH_HIGH_LEVEL",
                            action="ALARM",
                            target_tag="WET_WELL_HIGH_HIGH",
                            target_type="process_unit",
                            secondary_target_tag=None,
                            mode="AUTO",
                            priority=12,
                            confidence=0.78,
                            source_sentence=warning,
                            source_page=None,
                            section_heading="influent_pump_station",
                            explanation="Promoted warning: wet well high-high alarm.",
                            resolution_strategy=strategy,
                            unresolved_tokens=["symbolic_alarm_target"],
                            comments=["Promoted from warning into structured alarm rule."],
                            source_references=["warning-promotion:wetwell-high-high"],
                        )
                    )
                    handled = True

            if not handled and ("lead pump on" in lowered or "lag pump on" in lowered):
                pump_names = ("pmp-2001", "lead", "influent") if "lead" in lowered else ("pmp-2002", "lag", "standby")
                pump, strategy = self._find_entity_with_priority(
                    entity_index,
                    canonical_types={"pump"},
                    group="influent_pump_station",
                    preferred_names=pump_names,
                )
                source, source_strategy = self._find_entity_with_priority(
                    entity_index,
                    canonical_types={"level_switch", "level_transmitter"},
                    group="influent_pump_station",
                    preferred_names=("lit", "wet well"),
                )
                promoted.append(
                    ExtractedRuleDraft(
                        rule_group="influent_pump_station",
                        rule_type="start_stop",
                        source_tag=(source or {}).get("id", "WET_WELL_LEVEL"),
                        source_type=(source or {}).get("canonical_type", "level_transmitter"),
                        condition_kind="level",
                        operator=">=",
                        threshold="HIGH_LEVEL" if "lag" in lowered else "NORMAL_LEVEL",
                        threshold_name="HIGH_LEVEL" if "lag" in lowered else "NORMAL_LEVEL",
                        action="START",
                        target_tag=(pump or {}).get("id", "LAG_PUMP" if "lag" in lowered else "LEAD_PUMP"),
                        target_type=(pump or {}).get("canonical_type", "pump"),
                        secondary_target_tag=None,
                        mode="AUTO",
                        priority=13,
                        confidence=0.72,
                        source_sentence=warning,
                        source_page=None,
                        section_heading="influent_pump_station",
                        explanation="Promoted warning: pump duty/standby start.",
                        resolution_strategy=strategy if pump else source_strategy,
                        unresolved_tokens=[] if pump else ["lead_lag_assignment"],
                        comments=["Promoted from warning into structured rule."],
                        source_references=["warning-promotion:influent-pump-on"],
                    )
                )
                handled = True

            if not handled and ("manual override" in lowered or "auto/manual" in lowered):
                target, strategy = self._find_entity_with_priority(
                    entity_index,
                    canonical_types={"process_unit", "generic_device"},
                    preferred_names=("process", "train", "headworks"),
                )
                promoted.append(
                    ExtractedRuleDraft(
                        rule_group="modes",
                        rule_type="mode",
                        source_tag=(target or {}).get("id", "MODE_SELECTOR"),
                        source_type="generic_device",
                        condition_kind="mode",
                        operator="manual_command",
                        threshold="AUTO_MANUAL",
                        threshold_name="AUTO_MANUAL",
                        action="ENABLE",
                        target_tag=(target or {}).get("id", "PROCESS_TRAIN"),
                        target_type=(target or {}).get("canonical_type", "process_unit"),
                        secondary_target_tag=None,
                        mode="AUTO",
                        priority=30,
                        confidence=0.62,
                        source_sentence=warning,
                        source_page=None,
                        section_heading="modes",
                        explanation="Promoted warning: mode handling placeholder.",
                        resolution_strategy=strategy,
                        unresolved_tokens=["manual_override_logic"],
                        comments=["TODO: Manual override and AUTO/MANUAL mode handling inferred from narrative."],
                        source_references=["warning-promotion:modes"],
                    )
                )
                handled = True

            if handled:
                continue
            leftovers.append(warning)

        return promoted, leftovers

    @staticmethod
    def _bucket_warnings_by_group(warnings: list[str]) -> tuple[dict[str, list[str]], list[str]]:
        buckets: dict[str, list[str]] = {
            "influent_pump_station": [],
            "screening": [],
            "grit_removal": [],
            "aeration": [],
            "blower_package": [],
            "chemical_feed": [],
            "clarifier": [],
            "startup_shutdown": [],
            "modes": [],
        }
        leftovers: list[str] = []

        for warning in warnings:
            lowered = warning.lower()
            mapped = False
            if any(token in lowered for token in ("wet well", "influent", "pump station", "lead pump", "lag pump")):
                buckets["influent_pump_station"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("screen", "dp", "differential pressure")):
                buckets["screening"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("grit",)):
                buckets["grit_removal"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("aeration", "dissolved oxygen", "pid", "do analyzer")):
                buckets["aeration"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("blower", "header pressure")):
                buckets["blower_package"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("chemical", "dosing", "ratio", "fit-4501", "pmp-450")):
                buckets["chemical_feed"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("clarifier", "sludge", "blanket", "lit-2601", "pmp-260")):
                buckets["clarifier"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("startup", "shutdown", "emergency")):
                buckets["startup_shutdown"].append(warning)
                mapped = True
            elif any(token in lowered for token in ("manual", "override", "auto/manual", "local", "remote")):
                buckets["modes"].append(warning)
                mapped = True

            if not mapped:
                leftovers.append(warning)

        return buckets, leftovers

    def _next_project_version(self, project_id: str) -> int:
        row = postgres_client.fetch_one(
            """
            SELECT COALESCE(MAX(project_version), 0) AS max_version
            FROM logic_runs
            WHERE project_id = %s
            """,
            (project_id,),
        )
        return int((row or {}).get("max_version") or 0) + 1

    def _store_rules(
        self,
        project_id: str,
        run_id: str,
        project_version: int,
        rules: list[ControlRule],
        warnings: list[str],
        rejected: list[RejectedRuleCandidate],
        st_preview: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        postgres_client.execute(
            """
            INSERT INTO logic_runs (
                id, project_id, project_version, rules_count, warnings_count,
                status, st_preview, generator_version, warnings, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                project_id,
                project_version,
                len(rules),
                len(warnings),
                "completed",
                st_preview,
                self.generator_version,
                Json(warnings),
                now,
            ),
        )

        for rule in rules:
            rule.is_symbolic = self._is_symbolic_rule(rule)
            postgres_client.execute(
                """
                INSERT INTO control_rules (
                    id, project_id, logic_run_id, rule_group, rule_type, source_tag, source_type,
                    condition_kind, operator, threshold, threshold_name,
                    action, target_tag, target_type, secondary_target_tag,
                    mode, priority, confidence, source_sentence, source_page,
                    section_heading, explanation, resolution_strategy, is_symbolic, renderable, unresolved_tokens, comments,
                    display_text, st_preview, source_references, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                """,
                (
                    rule.id,
                    project_id,
                    run_id,
                    rule.rule_group,
                    rule.rule_type,
                    rule.source_tag,
                    rule.source_type,
                    rule.condition_kind,
                    rule.operator,
                    rule.threshold,
                    rule.threshold_name,
                    rule.action,
                    rule.target_tag,
                    rule.target_type,
                    rule.secondary_target_tag,
                    rule.mode,
                    rule.priority,
                    rule.confidence,
                    rule.source_sentence,
                    rule.source_page,
                    rule.section_heading,
                    rule.explanation,
                    rule.resolution_strategy,
                    rule.is_symbolic,
                    rule.renderable,
                    Json(rule.unresolved_tokens),
                    Json(rule.comments),
                    rule.display_text,
                    rule.st_preview,
                    Json(rule.source_references),
                    now,
                ),
            )

        for message in warnings:
            postgres_client.execute(
                """
                INSERT INTO logic_warnings (
                    id, project_id, logic_run_id, warning_type, message, source_sentence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid4()), project_id, run_id, "generation_warning", message, None, now),
            )

        for rejected_candidate in rejected:
            postgres_client.execute(
                """
                INSERT INTO logic_warnings (
                    id, project_id, logic_run_id, warning_type, message, source_sentence, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    project_id,
                    run_id,
                    "rejected_candidate",
                    rejected_candidate.reason,
                    rejected_candidate.source_sentence,
                    now,
                ),
            )

        # Persist render snapshot and rejected diagnostics into workspace file for traceability.
        logic_file = project_service.workspace_paths(project_id).control_logic / "main.st"
        logic_file.write_text(st_preview)
        rejected_file = project_service.workspace_paths(project_id).control_logic / "rejected_rules.json"
        rejected_file.write_text(json.dumps([item.model_dump() for item in rejected], indent=2))

    def _store_empty_run(self, project_id: str, run_id: str, project_version: int, message: str, st_preview: str) -> None:
        now = datetime.now(timezone.utc)
        postgres_client.execute(
            """
            INSERT INTO logic_runs (
                id, project_id, project_version, rules_count, warnings_count,
                status, st_preview, generator_version, warnings, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                project_id,
                project_version,
                0,
                1,
                "no_input",
                st_preview,
                self.generator_version,
                Json([message]),
                now,
            ),
        )
        postgres_client.execute(
            """
            INSERT INTO logic_warnings (
                id, project_id, logic_run_id, warning_type, message, source_sentence, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (str(uuid4()), project_id, run_id, "no_narrative", message, None, now),
        )

    def _fetch_rules(self, project_id: str, run_id: str | None = None) -> list[ControlRule]:
        run_sql = "AND logic_run_id = %s" if run_id else ""
        params: tuple = (project_id, run_id) if run_id else (project_id,)
        rows = postgres_client.fetch_all(
            f"""
            SELECT id::text AS id,
                   project_id::text AS project_id,
                   rule_group,
                   rule_type,
                   source_tag,
                   source_type,
                   condition_kind,
                   operator,
                   threshold,
                   threshold_name,
                   action,
                   target_tag,
                   target_type,
                   secondary_target_tag,
                   mode,
                   priority,
                   confidence,
                   source_sentence,
                   source_page,
                   section_heading,
                                     explanation,
                                     resolution_strategy,
                                     is_symbolic,
                   renderable,
                   unresolved_tokens,
                   comments,
                   display_text,
                   st_preview,
                   source_references,
                   created_at
            FROM control_rules
            WHERE project_id = %s
                            {run_sql}
            ORDER BY priority ASC, confidence DESC, created_at ASC
                        """,
                        params,
        )
        return [ControlRule.model_validate(dict(row)) for row in rows]

    def _load_latest_entities(self, project_id: str) -> list[EngineeringEntity]:
        rows = postgres_client.fetch_all(
            """
            SELECT em.payload AS payload
            FROM extracted_metadata em
            JOIN (
                SELECT id
                FROM parse_batches
                WHERE project_id = %s
                ORDER BY started_at DESC
                LIMIT 1
            ) latest ON latest.id = em.parse_batch_id
            WHERE em.project_id = %s
              AND em.category = 'engineering_entity'
            ORDER BY em.created_at ASC
            """,
            (project_id, project_id),
        )
        entities = [EngineeringEntity.model_validate(row.get("payload") or {}) for row in rows if row.get("payload")]
        if entities:
            return entities

        graph = graph_service.get_graph(project_id)
        fallback: list[EngineeringEntity] = []
        for node in graph.nodes:
            fallback.append(
                EngineeringEntity(
                    id=node.id,
                    tag=node.id,
                    canonical_type=node.node_type,
                    display_name=node.label,
                    aliases=[node.id, node.label],
                    process_unit=node.process_unit,
                    confidence=node.confidence,
                    is_synthetic=node.is_synthetic,
                    explanation=node.explanation,
                    source_references=node.source_references,
                )
            )
        return fallback

    def _loops_to_rules(self, project_id: str, loops: list) -> list[ControlRule]:
        rules: list[ControlRule] = []
        for index, loop in enumerate(loops, start=1):
            output_tag = loop.output_tag or f"{loop.actuator_tag}_CMD"
            rule = ControlRule(
                id=str(uuid4()),
                project_id=project_id,
                rule_group="general",
                rule_type="pid_loop" if loop.control_strategy.upper() == "PID" else "start_stop",
                source_tag=loop.sensor_tag,
                source_type="analyzer" if loop.control_strategy.upper() == "PID" else "level_transmitter",
                condition_kind="analyzer" if loop.control_strategy.upper() == "PID" else "boolean_state",
                operator=">=",
                threshold=loop.setpoint_tag or "SP",
                threshold_name=loop.setpoint_tag or "SP",
                action="MODULATE" if loop.control_strategy.upper() == "PID" else "START",
                target_tag=loop.actuator_tag,
                target_type="control_valve" if loop.control_strategy.upper() == "PID" else "pump",
                secondary_target_tag=None,
                mode="AUTO",
                priority=10 + index,
                confidence=loop.confidence,
                source_sentence=f"Discovered control loop {loop.loop_tag}",
                source_page=None,
                section_heading="control_loops",
                explanation=f"Loop strategy={loop.control_strategy} source={loop.sensor_tag} target={loop.actuator_tag}",
                resolution_strategy="graph_inference",
                is_symbolic=False,
                renderable=True,
                unresolved_tokens=[],
                comments=[],
                display_text=f"{loop.loop_tag}: {loop.sensor_tag} -> {loop.actuator_tag}",
                st_preview=(
                    f"IF {loop.sensor_tag} >= {loop.setpoint_tag or 'SP'} THEN\n"
                    f"    {output_tag} := {loop.sensor_tag};\n"
                    "END_IF;"
                ),
                source_references=["control_loop_engine"],
            )
            rules.append(rule)
        return rules

    @staticmethod
    def _build_st_preview_bundle(st_generation) -> str:
        file_map = {item.relative_path: item.content for item in st_generation.files}
        preferred = ["main.st", "utilities/utilities.st"]
        dynamic = sorted(path for path in file_map if path not in preferred)
        order = [item for item in preferred if item in file_map] + dynamic
        parts: list[str] = []
        for relative in order:
            content = (file_map.get(relative) or "").strip()
            if not content:
                continue
            parts.append(f"(* ===== FILE: {relative} ===== *)")
            parts.append(content)
            parts.append("")

        return "\n".join(parts).strip() + "\n"

    def generate(self, project_id: str, strategy: str = "deterministic") -> LogicGenerationResult:
        project_service.ensure_project(project_id)
        run_id = str(uuid4())
        entities = self._load_latest_entities(project_id)
        validation_report = engineering_validator.validate(project_id, entities)

        warnings = [item.message for item in validation_report.warnings]
        if validation_report.errors:
            warnings.extend([item.message for item in validation_report.errors])
            project_version = self._next_project_version(project_id)
            empty_code = "PROGRAM Main\n(* Engineering validation failed. ST generation aborted. *)\nEND_PROGRAM\n"
            self._store_empty_run(project_id, run_id, project_version, "Engineering validation failed.", empty_code)
            return LogicGenerationResult(
                project_id=project_id,
                file_name="main.st",
                code=empty_code,
                st_preview=empty_code,
                run_id=run_id,
                project_version=project_version,
                generator_version=self.generator_version,
                rules_count=0,
                warnings_count=len(warnings),
                rules=[],
                structured_rules=[],
                final_rendered_rules=[],
                symbolic_rendered_rules=[],
                groups={},
                rejected_candidates=[],
                rejected_rules=[],
                warnings=warnings,
                engineering_validation=validation_report,
            )

        loops = control_loop_engine.discover(project_id)
        completed_model = logic_completion_engine.complete(project_id, entities, loops, validation_report)
        confirmed_model, document_confirmation = document_confirmation_engine.confirm(project_id, entities, completed_model)
        st_generation = st_generator.generate(project_id, confirmed_model)
        st_validation = st_validator.validate(project_id, st_generation, model=confirmed_model)
        if not st_validation.valid:
            warnings.extend([item.message for item in st_validation.issues])
            project_version = self._next_project_version(project_id)
            empty_code = "PROGRAM Main\n(* ST validation failed. Check validation issues. *)\nEND_PROGRAM\n"
            self._store_empty_run(project_id, run_id, project_version, "ST validation failed.", empty_code)
            return LogicGenerationResult(
                project_id=project_id,
                file_name="main.st",
                code=empty_code,
                st_preview=empty_code,
                run_id=run_id,
                project_version=project_version,
                generator_version=self.generator_version,
                rules_count=0,
                warnings_count=len(warnings),
                rules=[],
                structured_rules=[],
                final_rendered_rules=[],
                symbolic_rendered_rules=[],
                groups={},
                rejected_candidates=[],
                rejected_rules=[],
                warnings=warnings,
                engineering_validation=validation_report,
                control_loops=loops,
                completed_logic_model=confirmed_model,
                st_validation=st_validation,
                document_confirmation=document_confirmation,
                confirmation_status=document_confirmation.confirmation_status,
            )

        st_preview = self._build_st_preview_bundle(st_generation)
        rules = self._loops_to_rules(project_id, loops)
        groups = {"general": rules}

        graph = graph_service.get_graph(project_id)
        io_mapping = io_mapping_engine.build(project_id, graph, confirmed_model)
        runtime_validation = runtime_deployer.validate_openplc_readiness(project_id, st_generation, io_mapping)
        st_validation = st_validator.validate(
            project_id,
            st_generation,
            model=confirmed_model,
            runtime_validation=runtime_validation,
        )
        if not st_validation.valid:
            warnings.extend([item.message for item in st_validation.issues])
            project_version = self._next_project_version(project_id)
            empty_code = "PROGRAM Main\n(* ST validation failed. Check validation issues. *)\nEND_PROGRAM\n"
            self._store_empty_run(project_id, run_id, project_version, "ST validation failed after runtime readiness checks.", empty_code)
            return LogicGenerationResult(
                project_id=project_id,
                file_name="main.st",
                code=empty_code,
                st_preview=empty_code,
                run_id=run_id,
                project_version=project_version,
                generator_version=self.generator_version,
                rules_count=0,
                warnings_count=len(warnings),
                rules=[],
                structured_rules=[],
                final_rendered_rules=[],
                symbolic_rendered_rules=[],
                groups={},
                rejected_candidates=[],
                rejected_rules=[],
                warnings=warnings,
                engineering_validation=validation_report,
                control_loops=loops,
                completed_logic_model=confirmed_model,
                st_validation=st_validation,
                io_mapping=io_mapping,
                runtime_validation=runtime_validation,
                document_confirmation=document_confirmation,
                confirmation_status=document_confirmation.confirmation_status,
            )
        simulation_validation = virtual_commissioning_service.run(project_id)
        version_snapshot = version_manager.snapshot(project_id, [item.relative_path for item in st_generation.files])

        generation_report = GenerationReport(
            project_id=project_id,
            generated_files=[
                GeneratedLogicFile(
                    relative_path=item.relative_path,
                    absolute_path=str(project_service.workspace_paths(project_id).control_logic / item.relative_path),
                    bytes_written=len(item.content.encode("utf-8")),
                )
                for item in st_generation.files
            ],
            issues=[
                GenerationValidationIssue(
                    code=issue.rule,
                    message=issue.message,
                    severity=issue.severity,
                    related_tags=issue.involved_tags,
                )
                for issue in st_validation.issues
            ],
            io_mapping=[
                IOMappingEntry(signal_tag=channel.signal_tag, io_type=channel.io_type, channel=channel.plc_channel)
                for channel in io_mapping.channels
            ],
            summary={
                "generated_files": len(st_generation.files),
                "validation_issues": len(st_validation.issues),
                "io_channels": len(io_mapping.channels),
                "evidence_equipment_items": len(document_confirmation.equipment_logic),
                "evidence_loop_items": len(document_confirmation.control_loops),
                "evidence_interlock_items": len(document_confirmation.interlocks),
                "evidence_sequence_items": len(document_confirmation.sequences),
                "evidence_alarm_items": len(document_confirmation.alarms),
            },
        )

        project_version = self._next_project_version(project_id)
        self._store_rules(project_id, run_id, project_version, rules, warnings, [], st_preview)
        final_rendered_rules, symbolic_rendered_rules = self._split_rendered_rules(rules)

        self.logger.info(
            "Control logic generation pipeline: project=%s loops=%s rules=%s",
            project_id,
            len(loops),
            len(rules),
        )

        return LogicGenerationResult(
            project_id=project_id,
            file_name="main.st",
            code=st_preview,
            st_preview=st_preview,
            run_id=run_id,
            project_version=project_version,
            generator_version=self.generator_version,
            rules_count=len(rules),
            warnings_count=len(warnings),
            rules=rules,
            structured_rules=rules,
            final_rendered_rules=final_rendered_rules,
            symbolic_rendered_rules=symbolic_rendered_rules,
            groups=groups,
            rejected_candidates=[],
            rejected_rules=[],
            warnings=warnings,
            engineering_validation=validation_report,
            control_loops=loops,
            completed_logic_model=confirmed_model,
            st_validation=st_validation,
            io_mapping=io_mapping,
            runtime_validation=runtime_validation,
            simulation_validation=simulation_validation,
            version_snapshot=version_snapshot,
            document_confirmation=document_confirmation,
            confirmation_status=document_confirmation.confirmation_status,
            generation_report=generation_report.model_dump(),
        )

    def list_rules(self, project_id: str) -> LogicGenerationResult:
        project_service.ensure_project(project_id)
        latest_run = postgres_client.fetch_one(
            """
            SELECT id::text AS id,
                   st_preview,
                   rules_count,
                   warnings_count,
                   generator_version,
                     project_version
            FROM logic_runs
            WHERE project_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (project_id,),
        )

        if latest_run is None:
            return LogicGenerationResult(
                project_id=project_id,
                file_name="main.st",
                code="",
                st_preview="",
                run_id="",
                project_version=None,
                generator_version=self.generator_version,
                rules_count=0,
                warnings_count=0,
                rules=[],
                structured_rules=[],
                final_rendered_rules=[],
                symbolic_rendered_rules=[],
                groups={},
                rejected_candidates=[],
                rejected_rules=[],
                warnings=[],
            )

        run_id = str(latest_run["id"])
        result = self.get_run(project_id, run_id)
        if result is None:
            return LogicGenerationResult(
                project_id=project_id,
                file_name="main.st",
                code="",
                st_preview="",
                run_id="",
                project_version=None,
                generator_version=self.generator_version,
                rules_count=0,
                warnings_count=0,
                rules=[],
                structured_rules=[],
                final_rendered_rules=[],
                symbolic_rendered_rules=[],
                groups={},
                rejected_candidates=[],
                rejected_rules=[],
                warnings=[],
            )
        return result

    def get_run(self, project_id: str, logic_run_id: str) -> LogicGenerationResult | None:
        project_service.ensure_project(project_id)
        run_row = postgres_client.fetch_one(
            """
            SELECT id::text AS id,
                   st_preview,
                   rules_count,
                   warnings_count,
                   generator_version,
                   project_version
            FROM logic_runs
            WHERE project_id = %s
              AND id = %s
            """,
            (project_id, logic_run_id),
        )
        if run_row is None:
            return None

        run_id = str(run_row["id"])
        rules = self._fetch_rules(project_id, run_id)
        warning_rows = postgres_client.fetch_all(
            """
            SELECT message
            FROM logic_warnings
            WHERE project_id = %s
              AND logic_run_id = %s
            ORDER BY created_at ASC
            """,
            (project_id, run_id),
        )
        warnings = [str(item.get("message") or "") for item in warning_rows if item.get("message")]

        groups: dict[str, list[ControlRule]] = {}
        for rule in rules:
            groups.setdefault(rule.rule_group, []).append(rule)

        st_preview = str(run_row.get("st_preview") or "")
        if not st_preview:
            st_preview, _ = st_renderer_service.render(rules, "latest", warnings)

        final_rendered_rules, symbolic_rendered_rules = self._split_rendered_rules(rules)

        return LogicGenerationResult(
            project_id=project_id,
            file_name="main.st",
            code=st_preview,
            st_preview=st_preview,
            run_id=run_id,
            project_version=int(run_row.get("project_version") or 0) or None,
            generator_version=str(run_row.get("generator_version") or self.generator_version),
            rules_count=len(rules),
            warnings_count=len(warnings),
            rules=rules,
            structured_rules=rules,
            final_rendered_rules=final_rendered_rules,
            symbolic_rendered_rules=symbolic_rendered_rules,
            groups=groups,
            rejected_candidates=[],
            rejected_rules=[],
            warnings=warnings,
        )

    def get_rule(self, project_id: str, rule_id: str) -> ControlRule | None:
        project_service.ensure_project(project_id)
        row = postgres_client.fetch_one(
            """
            SELECT id::text AS id,
                   project_id::text AS project_id,
                   rule_group,
                   rule_type,
                   source_tag,
                   source_type,
                   condition_kind,
                   operator,
                   threshold,
                   threshold_name,
                   action,
                   target_tag,
                   target_type,
                   secondary_target_tag,
                   mode,
                   priority,
                   confidence,
                   source_sentence,
                   source_page,
                   section_heading,
                   explanation,
                   resolution_strategy,
                   is_symbolic,
                   renderable,
                   unresolved_tokens,
                   comments,
                   display_text,
                   st_preview,
                   source_references,
                   created_at
            FROM control_rules
            WHERE project_id = %s AND id = %s
            """,
            (project_id, rule_id),
        )
        if row is None:
            return None
        return ControlRule.model_validate(dict(row))

    def get_latest(self, project_id: str) -> LogicGenerationResult:
        return self.list_rules(project_id)

    def validate_engineering_model(self, project_id: str):
        project_service.ensure_project(project_id)
        entities = self._load_latest_entities(project_id)
        return engineering_validator.validate(project_id, entities)

    def detect_control_loops(self, project_id: str):
        project_service.ensure_project(project_id)
        return control_loop_engine.discover(project_id)

    def validate_latest_st(self, project_id: str):
        project_service.ensure_project(project_id)
        result = self.get_latest(project_id)
        generation = STGenerationResult(
            project_id=project_id,
            output_root=str(project_service.workspace_paths(project_id).control_logic),
            files=[GeneratedSTFile(relative_path="main.st", content=result.code or "")],
        )
        return st_validator.validate(project_id, generation)

    def generate_io_mapping(self, project_id: str):
        project_service.ensure_project(project_id)
        report = self.validate_engineering_model(project_id)
        loops = self.detect_control_loops(project_id)
        entities = self._load_latest_entities(project_id)
        model = logic_completion_engine.complete(project_id, entities, loops, report)
        graph = graph_service.get_graph(project_id)
        return io_mapping_engine.build(project_id, graph, model)

    def runtime_validate(self, project_id: str):
        project_service.ensure_project(project_id)
        latest = self.get_latest(project_id)
        mapping = self.generate_io_mapping(project_id)
        generation = STGenerationResult(
            project_id=project_id,
            output_root=str(project_service.workspace_paths(project_id).control_logic),
            files=[GeneratedSTFile(relative_path="main.st", content=latest.code or "")],
        )
        return runtime_deployer.validate_openplc_readiness(project_id, generation, mapping)

    def run_virtual_commissioning(self, project_id: str):
        project_service.ensure_project(project_id)
        return virtual_commissioning_service.run(project_id)

    def create_version_snapshot(self, project_id: str):
        project_service.ensure_project(project_id)
        paths = project_service.workspace_paths(project_id).control_logic
        artifacts = []
        for relative in (
            "main.st",
            "equipment/equipment_routines.st",
            "control_loops/control_loops.st",
            "sequences/sequence_logic.st",
            "interlocks/interlocks.st",
            "alarms/alarms.st",
            "utilities/utilities.st",
        ):
            if (paths / relative).exists():
                artifacts.append(relative)
        return version_manager.snapshot(project_id, artifacts)


control_logic_service = ControlLogicService()
