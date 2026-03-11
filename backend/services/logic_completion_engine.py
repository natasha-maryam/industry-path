from __future__ import annotations

import logging

from models.logic import (
    AlarmRule,
    AlarmGroup,
    CompletedLogicModel,
    DiscoveredControlLoop,
    EngineeringValidationReport,
    EquipmentRoutine,
    InterlockRule,
    SequenceStep,
)
from models.pipeline import EngineeringEntity
from services.st_codegen_utils import st_codegen_utils


class LogicCompletionEngine:
    """Build a completed engineering logic model before ST generation."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _safe_stop_value(canonical_type: str) -> str:
        if canonical_type == "control_valve":
            return "0.0"
        return "FALSE"

    def complete(
        self,
        project_id: str,
        entities: list[EngineeringEntity],
        loops: list[DiscoveredControlLoop],
        validation_report: EngineeringValidationReport,
    ) -> CompletedLogicModel:
        routines: list[EquipmentRoutine] = []
        interlocks: list[InterlockRule] = []
        alarm_groups: list[AlarmGroup] = []
        entity_by_id = {entity.id: entity for entity in entities}

        for entity in sorted(entities, key=lambda item: item.id):
            if entity.canonical_type in {"pump", "control_valve", "valve", "blower", "chemical_system_device"}:
                routine_type = st_codegen_utils.classify_equipment_behavior(entity.canonical_type)
                output_owner = "loop_manager" if routine_type == "modulating" else "equipment_manager"
                auto_owner = "loop_manager" if routine_type == "modulating" else "equipment_manager"
                manual_owner = "equipment_manager" if routine_type in {"modulating", "open_close", "start_stop"} else "none"
                routines.append(
                    EquipmentRoutine(
                        equipment_tag=entity.id,
                        routine_name=f"{entity.id}_AUTO_ROUTINE",
                        routine_type="modulation" if routine_type == "modulating" else "start_stop",
                        command_tag=f"{entity.id}_CMD",
                        status_tag=f"{entity.id}_STATUS",
                        fault_tag=f"{entity.id}_FAULT",
                        equipment_type=entity.canonical_type,
                        permissive_tags=[f"{entity.id}_PERMISSIVE"],
                        auto_mode_tag=f"{entity.id}_AUTO",
                        manual_mode_tag=f"{entity.id}_MANUAL",
                        run_feedback_tag=f"{entity.id}_RUN_FB",
                        open_command_tag=f"{entity.id}_OPEN_CMD" if entity.canonical_type in {"valve", "control_valve"} else None,
                        close_command_tag=f"{entity.id}_CLOSE_CMD" if entity.canonical_type in {"valve", "control_valve"} else None,
                        output_tag=f"{entity.id}_OUT" if entity.canonical_type == "control_valve" else None,
                        safe_output_value=self._safe_stop_value(entity.canonical_type),
                        output_owner=output_owner,
                        auto_owner=auto_owner,
                        manual_owner=manual_owner,
                    )
                )

        typed_loops: list[DiscoveredControlLoop] = []
        for loop in loops:
            source_entity = entity_by_id.get(loop.sensor_tag)
            target_entity = entity_by_id.get(loop.actuator_tag)
            sensor_signal_type = st_codegen_utils.infer_signal_type(loop.sensor_tag, source_entity.canonical_type if source_entity else None)
            output_tag, command_tag = st_codegen_utils.infer_loop_output_tags(
                loop.actuator_tag,
                target_entity.canonical_type if target_entity else None,
                loop.control_strategy,
            )
            chosen_output = loop.output_tag_analog or loop.output_tag or output_tag
            output_type_hint = target_entity.canonical_type if target_entity else None
            output_signal_type = st_codegen_utils.infer_signal_type(
                chosen_output,
                output_type_hint,
            )
            typed_loop = loop.model_copy(
                update={
                    "pv_tag": loop.pv_tag or loop.sensor_tag,
                    "sp_tag": loop.sp_tag or loop.setpoint_tag or f"{loop.sensor_tag}_SP",
                    "output_tag": chosen_output,
                    "output_tag_analog": chosen_output if st_codegen_utils.is_real_signal(chosen_output, output_type_hint, role="analog_output") else None,
                    "command_tag_bool": command_tag,
                    "sensor_signal_type": sensor_signal_type,
                    "output_signal_type": output_signal_type,
                    "output_owner": "loop_manager" if output_signal_type == "analog" else "equipment_manager",
                    "auto_owner": "loop_manager" if output_signal_type == "analog" else "equipment_manager",
                    "manual_owner": "equipment_manager",
                    "fail_safe_output_value": self._safe_stop_value(target_entity.canonical_type if target_entity else "pump"),
                    "interlock_action_type": "force_output" if output_signal_type == "analog" else "force_command",
                    "interlock_inhibit_tag": f"{loop.actuator_tag}_ENABLE",
                    "mode_tag": f"{loop.actuator_tag}_AUTO",
                    "enable_tag": f"{loop.actuator_tag}_ENABLE",
                    "output_min": 0.0,
                    "output_max": 100.0,
                }
            )
            typed_loops.append(typed_loop)

            threshold_map = st_codegen_utils.infer_threshold_tags(loop.sensor_tag)
            interlocks.append(
                InterlockRule(
                    interlock_id=f"ILK-{loop.sensor_tag}-{loop.actuator_tag}",
                    source_tag=loop.sensor_tag,
                    source_type=source_entity.canonical_type if source_entity else None,
                    target_tag=loop.actuator_tag,
                    comparator=">=" if sensor_signal_type == "analog" else "==",
                    threshold_tag=threshold_map["INTERLOCK"] if sensor_signal_type == "analog" else "TRUE",
                    target_command_tag=loop.command_tag_bool or f"{loop.actuator_tag}_CMD",
                    target_output_tag=loop.output_tag_analog,
                    inhibit_tag=f"{loop.actuator_tag}_ENABLE",
                    interlock_action_type="force_output" if (loop.output_signal_type == "analog" or loop.output_tag_analog) else "force_command",
                    safe_value=self._safe_stop_value(target_entity.canonical_type if target_entity else "pump"),
                    action="inhibit",
                    rationale="Default protection interlock inferred from discovered loop.",
                )
            )

        if typed_loops:
            alarm_rules: list[AlarmRule] = []
            for loop in typed_loops:
                source_entity = entity_by_id.get(loop.sensor_tag)
                threshold_map = st_codegen_utils.infer_threshold_tags(loop.sensor_tag)
                source_type = source_entity.canonical_type if source_entity else None
                signal_type = st_codegen_utils.infer_signal_type(loop.sensor_tag, source_type)

                if signal_type == "analog":
                    alarm_rules.extend(
                        [
                            AlarmRule(
                                source_tag=loop.sensor_tag,
                                source_type=source_type,
                                alarm_tag=f"ALM_{loop.sensor_tag}_HI",
                                alarm_type="HI",
                                comparator=">=",
                                threshold_tag=threshold_map["HI"],
                                rationale="Inferred high alarm from discovered analog control loop.",
                            ),
                            AlarmRule(
                                source_tag=loop.sensor_tag,
                                source_type=source_type,
                                alarm_tag=f"ALM_{loop.sensor_tag}_HH",
                                alarm_type="HH",
                                comparator=">=",
                                threshold_tag=threshold_map["HH"],
                                rationale="Inferred high-high alarm from discovered analog control loop.",
                            ),
                            AlarmRule(
                                source_tag=loop.sensor_tag,
                                source_type=source_type,
                                alarm_tag=f"ALM_{loop.sensor_tag}_LO",
                                alarm_type="LO",
                                comparator="<=",
                                threshold_tag=threshold_map["LO"],
                                rationale="Inferred low alarm from discovered analog control loop.",
                            ),
                            AlarmRule(
                                source_tag=loop.sensor_tag,
                                source_type=source_type,
                                alarm_tag=f"ALM_{loop.sensor_tag}_LL",
                                alarm_type="LL",
                                comparator="<=",
                                threshold_tag=threshold_map["LL"],
                                rationale="Inferred low-low alarm from discovered analog control loop.",
                            ),
                        ]
                    )

            for routine in routines:
                if routine.fault_tag:
                    alarm_rules.append(
                        AlarmRule(
                            source_tag=routine.fault_tag,
                            source_type="fault",
                            alarm_tag=f"ALM_{routine.equipment_tag}_FAULT",
                            alarm_type="FAULT",
                            comparator="==",
                            threshold_tag="TRUE",
                            rationale="Equipment fault alarm inferred from equipment routine metadata.",
                        )
                    )

            alarm_groups.append(
                AlarmGroup(
                    group_name="PROCESS_CONTROL_ALARMS",
                    alarm_tags=sorted({rule.alarm_tag for rule in alarm_rules}),
                    alarm_rules=alarm_rules,
                    severity="high",
                )
            )

        startup_sequence = self._build_startup_sequence(routines)
        shutdown_sequence = self._build_shutdown_sequence(routines)

        fallback_notes = [
            "Fallback logic defaults command outputs to SAFE state on missing permissives.",
            "Default command/status/fault tags were inferred from equipment tags.",
        ]

        unresolved_items: list[str] = []
        if validation_report.errors:
            unresolved_items.extend([f"Validation error: {item.message}" for item in validation_report.errors])
        if not typed_loops:
            unresolved_items.append("No control loops were inferred from graph relationships.")

        model = CompletedLogicModel(
            project_id=project_id,
            loops=typed_loops,
            equipment_routines=routines,
            alarm_groups=alarm_groups,
            interlocks=interlocks,
            startup_sequence=startup_sequence,
            shutdown_sequence=shutdown_sequence,
            fallback_logic_notes=fallback_notes,
            unresolved_items=unresolved_items,
        )
        self.logger.info(
            "Logic completion finished: project=%s routines=%s loops=%s unresolved=%s",
            project_id,
            len(routines),
            len(loops),
            len(unresolved_items),
        )
        return model

    @staticmethod
    def _routine_startup_priority(routine: EquipmentRoutine) -> tuple[int, str]:
        behavior = st_codegen_utils.classify_equipment_behavior(routine.equipment_type)
        if behavior == "open_close":
            order = 10
        elif behavior == "start_stop":
            order = 20
        elif behavior == "modulating":
            order = 30
        else:
            order = 40
        return order, routine.equipment_tag

    def _startup_command_for_routine(self, routine: EquipmentRoutine) -> str | None:
        behavior = st_codegen_utils.classify_equipment_behavior(routine.equipment_type)
        if behavior == "open_close":
            return routine.open_command_tag or routine.command_tag
        if behavior == "modulating":
            return routine.auto_mode_tag or routine.command_tag
        return routine.command_tag

    def _shutdown_command_for_routine(self, routine: EquipmentRoutine) -> str | None:
        behavior = st_codegen_utils.classify_equipment_behavior(routine.equipment_type)
        if behavior == "open_close":
            return routine.close_command_tag or routine.command_tag
        if behavior == "modulating":
            return routine.auto_mode_tag or routine.command_tag
        return routine.command_tag

    def _build_startup_sequence(self, routines: list[EquipmentRoutine]) -> list[SequenceStep]:
        ordered = sorted(routines, key=self._routine_startup_priority)
        sequence: list[SequenceStep] = []
        step_number = 10

        for routine in ordered:
            command_tags: list[str] = []
            if routine.command_tag:
                command_tags.append(routine.command_tag)
            preferred = self._startup_command_for_routine(routine)
            if preferred and preferred not in command_tags:
                command_tags.append(preferred)
            if not command_tags:
                continue
            transition_tag = routine.status_tag or "PERMISSIVES_OK"
            for command_tag in command_tags:
                sequence.append(
                    SequenceStep(
                        step_number=step_number,
                        description=f"Startup command for {routine.equipment_tag}",
                        trigger_tag="STARTUP_CMD",
                        transition_tag=transition_tag,
                        transition_kind="external",
                        command_tag=command_tag,
                        expected_state=step_number,
                    )
                )
                step_number += 10

        sequence.append(
            SequenceStep(
                step_number=step_number,
                description="Process startup hold confirmation",
                trigger_tag="STARTUP_CMD",
                transition_tag="STARTUP_HOLD_OK",
                transition_kind="external",
                command_tag="PROCESS_RUNNING",
                expected_state=step_number,
            )
        )
        return sequence

    def _build_shutdown_sequence(self, routines: list[EquipmentRoutine]) -> list[SequenceStep]:
        ordered = sorted(routines, key=self._routine_startup_priority, reverse=True)
        sequence: list[SequenceStep] = []
        step_number = 10

        for index, routine in enumerate(ordered):
            command_tags: list[str] = []
            if routine.command_tag:
                command_tags.append(routine.command_tag)
            preferred = self._shutdown_command_for_routine(routine)
            if preferred and preferred not in command_tags:
                command_tags.append(preferred)
            if not command_tags:
                continue
            transition_tag = "SHUTDOWN_CMD" if index == 0 else "STOP_CONFIRM"
            for command_tag in command_tags:
                sequence.append(
                    SequenceStep(
                        step_number=step_number,
                        description=f"Shutdown command for {routine.equipment_tag}",
                        trigger_tag="SHUTDOWN_CMD",
                        transition_tag=transition_tag,
                        transition_kind="external",
                        command_tag=command_tag,
                        expected_state=step_number,
                    )
                )
                step_number += 10

        sequence.append(
            SequenceStep(
                step_number=step_number,
                description="Shutdown hold confirmation",
                trigger_tag="SHUTDOWN_CMD",
                transition_tag="SHUTDOWN_HOLD_OK",
                transition_kind="external",
                command_tag="PROCESS_STOPPED",
                expected_state=step_number,
            )
        )
        return sequence


logic_completion_engine = LogicCompletionEngine()
