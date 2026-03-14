from __future__ import annotations

import logging
import re
from pathlib import Path

from models.logic import CompletedLogicModel, GeneratedSTFile, STGenerationResult
from services.project_service import project_service
from services.st_codegen_utils import st_codegen_utils


class STGenerator:
    """Deterministic vendor-agnostic ST generation with per-routine output files."""

    REQUIRED_MODULE_ORDER = ["interlocks", "sequences", "equipment", "loops", "alarms"]
    EXECUTION_LAYER_ORDER = ["system", "interlocks", "sequences", "equipment", "loops", "alarms"]

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _write_file(base_dir: Path, relative_path: str, content: str) -> GeneratedSTFile:
        target = base_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return GeneratedSTFile(relative_path=relative_path, content=content)

    @staticmethod
    def _coerce_bool_literal(value: str | None, default: str = "FALSE") -> str:
        if not value:
            return default
        upper = str(value).strip().upper()
        if upper in {"TRUE", "FALSE"}:
            return upper
        return default

    @staticmethod
    def _coerce_real_literal(value: str | None, default: float = 0.0) -> str:
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return f"{default:.1f}"

    @staticmethod
    def _var_type_from_signal(signal_type: str) -> str:
        if signal_type == "analog":
            return "REAL"
        if signal_type == "int":
            return "INT"
        return "BOOL"

    def _symbol(self, raw: str | None) -> str:
        return st_codegen_utils.normalize_symbol(raw)

    def _file_stem(self, raw: str | None) -> str:
        symbol = self._symbol(raw)
        stem = re.sub(r"[^a-z0-9_]+", "_", symbol.lower())
        return re.sub(r"_+", "_", stem).strip("_") or "routine"

    def _block_suffix(self, raw: str | None) -> str:
        symbol = self._symbol(raw)
        return re.sub(r"[^A-Z0-9_]+", "_", symbol.upper()).strip("_") or "ROUTINE"

    def _collect_symbol_types(self, model: CompletedLogicModel) -> dict[str, str]:
        symbol_types: dict[str, str] = {
            "STARTUP_CMD": "BOOL",
            "SHUTDOWN_CMD": "BOOL",
            "PERMISSIVES_OK": "BOOL",
            "AUTO_ENABLE_CMD": "BOOL",
            "STOP_ALL_CMD": "BOOL",
            "LATCH_SHUTDOWN": "BOOL",
            "STARTUP_HOLD_OK": "BOOL",
            "SHUTDOWN_HOLD_OK": "BOOL",
            "STOP_CONFIRM": "BOOL",
            "STARTUP_ACTIVE": "BOOL",
            "SHUTDOWN_ACTIVE": "BOOL",
            "PROCESS_RUNNING": "BOOL",
            "PROCESS_STOPPED": "BOOL",
            "CURRENT_PLANT_STATE": "PLANT_STATE",
            "NEXT_PLANT_STATE": "PLANT_STATE",
            "PLANT_START_CMD": "BOOL",
            "PLANT_STOP_CMD": "BOOL",
            "PLANT_FAULT_ACTIVE": "BOOL",
        }

        for routine in model.equipment_routines:
            if routine.command_tag:
                symbol_types[self._symbol(routine.command_tag)] = "BOOL"
            if routine.status_tag:
                symbol_types[self._symbol(routine.status_tag)] = "BOOL"
            if routine.fault_tag:
                symbol_types[self._symbol(routine.fault_tag)] = "BOOL"
            for permissive in routine.permissive_tags:
                symbol_types[self._symbol(permissive)] = "BOOL"
            if routine.auto_mode_tag:
                symbol_types[self._symbol(routine.auto_mode_tag)] = "BOOL"
            if routine.manual_mode_tag:
                symbol_types[self._symbol(routine.manual_mode_tag)] = "BOOL"
            if routine.run_feedback_tag:
                symbol_types[self._symbol(routine.run_feedback_tag)] = "BOOL"
            if routine.open_command_tag:
                symbol_types[self._symbol(routine.open_command_tag)] = "BOOL"
            if routine.close_command_tag:
                symbol_types[self._symbol(routine.close_command_tag)] = "BOOL"
            if routine.output_tag:
                symbol_types[self._symbol(routine.output_tag)] = "REAL"
            symbol_types[self._symbol(st_codegen_utils.normalize_tag_with_suffix(routine.equipment_tag, "RUN_CMD"))] = "BOOL"

        for loop in model.loops:
            pv = self._symbol(loop.pv_tag or loop.sensor_tag)
            sp = self._symbol(loop.sp_tag or loop.setpoint_tag or st_codegen_utils.normalize_tag_with_suffix(loop.sensor_tag, "SP"))
            out = self._symbol(loop.output_tag_analog or loop.output_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "OUT"))
            symbol_types[pv] = self._var_type_from_signal(loop.sensor_signal_type)
            symbol_types[sp] = "REAL"
            symbol_types[out] = "REAL" if loop.output_signal_type == "analog" else "BOOL"
            symbol_types[self._symbol(loop.mode_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "AUTO"))] = "BOOL"
            symbol_types[self._symbol(loop.enable_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "ENABLE"))] = "BOOL"

            threshold = st_codegen_utils.infer_threshold_tags(loop.sensor_tag)
            symbol_types[self._symbol(threshold["HI"])] = "REAL"
            symbol_types[self._symbol(threshold["HH"])] = "REAL"
            symbol_types[self._symbol(threshold["LO"])] = "REAL"
            symbol_types[self._symbol(threshold["LL"])] = "REAL"

        for interlock in model.interlocks:
            source_signal = st_codegen_utils.infer_signal_type(interlock.source_tag, interlock.source_type)
            symbol_types[self._symbol(interlock.source_tag)] = self._var_type_from_signal(source_signal)
            if interlock.target_command_tag:
                symbol_types[self._symbol(interlock.target_command_tag)] = "BOOL"
            if interlock.target_output_tag:
                symbol_types[self._symbol(interlock.target_output_tag)] = "REAL"
            if interlock.inhibit_tag:
                symbol_types[self._symbol(interlock.inhibit_tag)] = "BOOL"
            if interlock.threshold_tag and interlock.threshold_tag.upper() not in {"TRUE", "FALSE"}:
                symbol_types[self._symbol(interlock.threshold_tag)] = "REAL" if source_signal == "analog" else "BOOL"

        for group in model.alarm_groups:
            for alarm in group.alarm_rules:
                source_signal = st_codegen_utils.infer_signal_type(alarm.source_tag, alarm.source_type)
                symbol_types[self._symbol(alarm.source_tag)] = self._var_type_from_signal(source_signal)
                symbol_types[self._symbol(alarm.alarm_tag)] = "BOOL"
                if alarm.threshold_tag and alarm.threshold_tag.upper() not in {"TRUE", "FALSE"}:
                    symbol_types[self._symbol(alarm.threshold_tag)] = "REAL" if source_signal == "analog" else "BOOL"

        for step in model.startup_sequence + model.shutdown_sequence:
            if step.trigger_tag:
                symbol_types[self._symbol(step.trigger_tag)] = "BOOL"
            if step.transition_tag and step.transition_tag not in {"EXECUTE_RESET"}:
                symbol_types[self._symbol(step.transition_tag)] = "BOOL"
            if step.command_tag:
                symbol_types[self._symbol(step.command_tag)] = "BOOL"

        return symbol_types

    @staticmethod
    def _render_external_vars(symbol_types: dict[str, str], symbols: set[str]) -> list[str]:
        lines = ["VAR_EXTERNAL"]
        for symbol in sorted(symbols):
            if symbol in symbol_types:
                lines.append(f"    {symbol} : {symbol_types[symbol]};")
        lines.append("END_VAR")
        return lines

    @staticmethod
    def _render_local_vars(local_vars: list[str]) -> list[str]:
        if not local_vars:
            return []
        lines = ["VAR"]
        lines.extend(local_vars)
        lines.append("END_VAR")
        return lines

    def _render_function_block(
        self,
        block_name: str,
        symbol_types: dict[str, str],
        external_symbols: set[str],
        body_lines: list[str],
        local_vars: list[str] | None = None,
    ) -> str:
        external_symbols = self._ensure_complete_declarations(
            symbol_types=symbol_types,
            external_symbols=external_symbols,
            body_lines=body_lines,
            local_vars=local_vars,
        )
        lines = [f"FUNCTION_BLOCK {block_name}"]
        lines.extend(self._render_external_vars(symbol_types, external_symbols))
        if local_vars:
            lines.extend(self._render_local_vars(local_vars))
        lines.append("")
        lines.extend(body_lines)
        lines.append("END_FUNCTION_BLOCK")
        return "\n".join(lines).strip() + "\n"

    def _ensure_complete_declarations(
        self,
        symbol_types: dict[str, str],
        external_symbols: set[str],
        body_lines: list[str],
        local_vars: list[str] | None,
    ) -> set[str]:
        local_declared: set[str] = set()
        if local_vars:
            for line in local_vars:
                match = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*:\s*", line)
                if match:
                    local_declared.add(match.group(1))

        code = "\n".join(body_lines)
        used_symbols = set(re.findall(r"\b[A-Z_][A-Z0-9_]*\b", code))
        reserved = {
            "IF",
            "THEN",
            "ELSE",
            "ELSIF",
            "END_IF",
            "CASE",
            "OF",
            "END_CASE",
            "TRUE",
            "FALSE",
            "AND",
            "OR",
            "NOT",
            "FUNCTION_BLOCK",
            "FUNCTION",
            "VAR",
            "VAR_INPUT",
            "VAR_OUTPUT",
            "VAR_EXTERNAL",
            "END_VAR",
            "REAL",
            "BOOL",
            "INT",
            "CLX_CLAMPREAL",
            "FB_R_TRIG",
            "PLANT_STATE",
            "PLANT_STOPPED",
            "PLANT_STARTING",
            "PLANT_RUNNING",
            "PLANT_STOPPING",
            "PLANT_FAULT",
        }

        missing_symbols = used_symbols - external_symbols - local_declared - reserved
        for symbol in sorted(missing_symbols):
            external_symbols.add(symbol)
            if symbol not in symbol_types:
                symbol_types[symbol] = st_codegen_utils.infer_st_type(symbol)
        return external_symbols

    def _render_equipment_file(self, routine, symbol_types: dict[str, str]) -> str:
        behavior = st_codegen_utils.classify_equipment_behavior(routine.equipment_type)
        eq_tag = routine.equipment_tag

        cmd = self._symbol(routine.command_tag)
        status = self._symbol(routine.status_tag)
        fault = self._symbol(routine.fault_tag)
        auto_mode = self._symbol(routine.auto_mode_tag)
        manual_mode = self._symbol(routine.manual_mode_tag) if routine.manual_mode_tag else f"(NOT {auto_mode})"
        run_feedback = self._symbol(routine.run_feedback_tag)
        run_cmd = self._symbol(st_codegen_utils.normalize_tag_with_suffix(eq_tag, "RUN_CMD"))
        permissive = self._symbol(routine.permissive_tags[0]) if routine.permissive_tags else "PERMISSIVES_OK"
        open_cmd = self._symbol(routine.open_command_tag) if routine.open_command_tag else "FALSE"
        close_cmd = self._symbol(routine.close_command_tag) if routine.close_command_tag else "FALSE"
        analog_out = self._symbol(routine.output_tag) if routine.output_tag else self._symbol(st_codegen_utils.normalize_tag_with_suffix(eq_tag, "OUT"))
        safe_output = self._coerce_real_literal(routine.safe_output_value, default=0.0)

        external_symbols: set[str] = {
            status,
            fault,
            auto_mode,
            permissive,
            run_feedback,
            run_cmd,
            "CURRENT_PLANT_STATE",
        }
        if behavior in {"start_stop", "open_close"}:
            external_symbols.add(cmd)
        if behavior == "modulating":
            external_symbols.add(analog_out)
            if routine.output_owner == "equipment_manager":
                external_symbols.add(open_cmd)
                external_symbols.add(close_cmd)
            if routine.manual_mode_tag:
                external_symbols.add(self._symbol(routine.manual_mode_tag))
        elif behavior == "open_close":
            external_symbols.add(open_cmd)
            external_symbols.add(close_cmd)

        body: list[str] = []
        local_vars: list[str] = []
        if behavior == "modulating":
            equipment_writes_output = routine.output_owner == "equipment_manager" and routine.auto_owner != "loop_manager"
            base = self._block_suffix(eq_tag)
            fault_active = f"FAULT_ACTIVE_{base}"
            permissive_ok = f"PERMISSIVE_OK_{base}"
            auto_active = f"AUTO_ACTIVE_{base}"
            manual_active = f"MANUAL_ACTIVE_{base}"
            open_active = f"OPEN_ACTIVE_{base}"
            close_active = f"CLOSE_ACTIVE_{base}"
            output_active = f"OUTPUT_ACTIVE_{base}"
            plant_commands_enabled = f"PLANT_COMMANDS_ENABLED_{base}"
            local_vars.extend(
                [
                    f"    {fault_active} : BOOL := FALSE;",
                    f"    {permissive_ok} : BOOL := FALSE;",
                    f"    {auto_active} : BOOL := FALSE;",
                    f"    {manual_active} : BOOL := FALSE;",
                    f"    {open_active} : BOOL := FALSE;",
                    f"    {close_active} : BOOL := FALSE;",
                    f"    {output_active} : BOOL := FALSE;",
                    f"    {plant_commands_enabled} : BOOL := FALSE;",
                ]
            )
            body.append(f"IF CURRENT_PLANT_STATE = PLANT_RUNNING THEN")
            body.append(f"    {plant_commands_enabled} := TRUE;")
            body.append("ELSIF CURRENT_PLANT_STATE = PLANT_STARTING THEN")
            body.append(f"    {plant_commands_enabled} := TRUE;")
            body.append("ELSE")
            body.append(f"    {plant_commands_enabled} := FALSE;")
            body.append("END_IF;")
            body.append(f"{fault_active} := {fault};")
            body.append(f"{permissive_ok} := {permissive};")
            body.append(f"{auto_active} := {auto_mode};")
            body.append(f"{manual_active} := {manual_mode};")
            body.append(f"IF {plant_commands_enabled} THEN")
            body.append(f"    {open_active} := {open_cmd};")
            body.append(f"    {close_active} := {close_cmd};")
            body.append("ELSE")
            body.append(f"    {open_active} := FALSE;")
            body.append(f"    {close_active} := FALSE;")
            body.append("END_IF;")
            body.append(f"{output_active} := {analog_out} > 0.1;")
            body.append(f"IF {fault_active} THEN")
            if equipment_writes_output:
                body.append(f"    {analog_out} := {safe_output};")
            body.append(f"    {status} := FALSE;")
            body.append(f"ELSIF NOT {plant_commands_enabled} THEN")
            if equipment_writes_output:
                body.append(f"    {analog_out} := {safe_output};")
            body.append(f"    {status} := FALSE;")
            body.append(f"ELSIF NOT {permissive_ok} THEN")
            if equipment_writes_output:
                body.append(f"    {analog_out} := {safe_output};")
            body.append(f"    {status} := FALSE;")
            body.append(f"ELSIF {auto_active} THEN")
            if routine.auto_owner == "loop_manager":
                body.append(f"    IF {output_active} THEN")
                body.append(f"        {status} := TRUE;")
                body.append("    ELSIF {run_feedback} THEN".format(run_feedback=run_feedback))
                body.append(f"        {status} := TRUE;")
                body.append("    ELSE")
                body.append(f"        {status} := FALSE;")
                body.append("    END_IF;")
            else:
                body.append(f"    IF {open_active} THEN")
                body.append(f"        {analog_out} := CLX_ClampReal({analog_out} + 2.0, 0.0, 100.0);")
                body.append(f"    ELSIF {close_active} THEN")
                body.append(f"        {analog_out} := CLX_ClampReal({analog_out} - 2.0, 0.0, 100.0);")
                body.append("    END_IF;")
                body.append(f"    {output_active} := {analog_out} > 0.1;")
                body.append(f"    IF {output_active} THEN")
                body.append(f"        {status} := TRUE;")
                body.append("    ELSIF {run_feedback} THEN".format(run_feedback=run_feedback))
                body.append(f"        {status} := TRUE;")
                body.append("    ELSE")
                body.append(f"        {status} := FALSE;")
                body.append("    END_IF;")
            body.append(f"ELSIF {manual_active} THEN")
            if routine.manual_owner == "equipment_manager" and equipment_writes_output:
                body.append(f"    IF {open_active} THEN")
                body.append(f"        {analog_out} := CLX_ClampReal({analog_out} + 2.0, 0.0, 100.0);")
                body.append(f"    ELSIF {close_active} THEN")
                body.append(f"        {analog_out} := CLX_ClampReal({analog_out} - 2.0, 0.0, 100.0);")
                body.append("    END_IF;")
            body.append(f"    {output_active} := {analog_out} > 0.1;")
            body.append(f"    IF {output_active} THEN")
            body.append(f"        {status} := TRUE;")
            body.append("    ELSIF {run_feedback} THEN".format(run_feedback=run_feedback))
            body.append(f"        {status} := TRUE;")
            body.append("    ELSE")
            body.append(f"        {status} := FALSE;")
            body.append("    END_IF;")
            body.append("ELSE")
            body.append(f"    {output_active} := {analog_out} > 0.1;")
            body.append(f"    IF {output_active} THEN")
            body.append(f"        {status} := TRUE;")
            body.append("    ELSIF {run_feedback} THEN".format(run_feedback=run_feedback))
            body.append(f"        {status} := TRUE;")
            body.append("    ELSE")
            body.append(f"        {status} := FALSE;")
            body.append("    END_IF;")
            body.append("END_IF;")
        elif behavior == "open_close":
            base = self._block_suffix(eq_tag)
            fault_active = f"FAULT_ACTIVE_{base}"
            permissive_ok = f"PERMISSIVE_OK_{base}"
            auto_active = f"AUTO_ACTIVE_{base}"
            cmd_valid = f"CMD_VALID_{base}"
            open_active = f"OPEN_ACTIVE_{base}"
            close_active = f"CLOSE_ACTIVE_{base}"
            plant_commands_enabled = f"PLANT_COMMANDS_ENABLED_{base}"
            local_vars.extend(
                [
                    f"    {fault_active} : BOOL := FALSE;",
                    f"    {permissive_ok} : BOOL := FALSE;",
                    f"    {auto_active} : BOOL := FALSE;",
                    f"    {cmd_valid} : BOOL := FALSE;",
                    f"    {open_active} : BOOL := FALSE;",
                    f"    {close_active} : BOOL := FALSE;",
                    f"    {plant_commands_enabled} : BOOL := FALSE;",
                ]
            )
            body.append(f"IF CURRENT_PLANT_STATE = PLANT_RUNNING THEN")
            body.append(f"    {plant_commands_enabled} := TRUE;")
            body.append("ELSIF CURRENT_PLANT_STATE = PLANT_STARTING THEN")
            body.append(f"    {plant_commands_enabled} := TRUE;")
            body.append("ELSE")
            body.append(f"    {plant_commands_enabled} := FALSE;")
            body.append("END_IF;")
            body.append(f"{fault_active} := {fault};")
            body.append(f"{permissive_ok} := {permissive};")
            body.append(f"{auto_active} := {auto_mode};")
            body.append(f"IF {plant_commands_enabled} THEN")
            body.append(f"    {cmd_valid} := {cmd};")
            body.append(f"    {open_active} := {open_cmd};")
            body.append(f"    {close_active} := {close_cmd};")
            body.append("ELSE")
            body.append(f"    {cmd_valid} := FALSE;")
            body.append(f"    {open_active} := FALSE;")
            body.append(f"    {close_active} := FALSE;")
            body.append("END_IF;")
            body.append(f"IF {fault_active} THEN")
            body.append(f"    {status} := FALSE;")
            body.append(f"ELSIF {auto_active} THEN")
            body.append(f"    IF {permissive_ok} THEN")
            body.append(f"        IF {open_active} THEN")
            body.append(f"            {status} := TRUE;")
            body.append(f"        ELSIF {cmd_valid} THEN")
            body.append(f"            {status} := TRUE;")
            body.append(f"        ELSIF {close_active} THEN")
            body.append(f"            {status} := FALSE;")
            body.append(f"        ELSE")
            body.append(f"            {status} := FALSE;")
            body.append("        END_IF;")
            body.append("    ELSE")
            body.append(f"        {status} := FALSE;")
            body.append("    END_IF;")
            body.append("ELSE")
            body.append(f"    {status} := FALSE;")
            body.append("END_IF;")
        else:
            base = self._block_suffix(eq_tag)
            cmd_valid = f"CMD_VALID_{base}"
            permissive_ok = f"PERMISSIVE_OK_{base}"
            fault_active = f"FAULT_ACTIVE_{base}"
            auto_active = f"AUTO_ACTIVE_{base}"
            run_feedback_active = f"RUN_FEEDBACK_ACTIVE_{base}"
            plant_commands_enabled = f"PLANT_COMMANDS_ENABLED_{base}"
            local_vars.extend(
                [
                    f"    {cmd_valid} : BOOL := FALSE;",
                    f"    {permissive_ok} : BOOL := FALSE;",
                    f"    {fault_active} : BOOL := FALSE;",
                    f"    {auto_active} : BOOL := FALSE;",
                    f"    {run_feedback_active} : BOOL := FALSE;",
                    f"    {plant_commands_enabled} : BOOL := FALSE;",
                ]
            )
            body.append(f"IF CURRENT_PLANT_STATE = PLANT_RUNNING THEN")
            body.append(f"    {plant_commands_enabled} := TRUE;")
            body.append("ELSIF CURRENT_PLANT_STATE = PLANT_STARTING THEN")
            body.append(f"    {plant_commands_enabled} := TRUE;")
            body.append("ELSE")
            body.append(f"    {plant_commands_enabled} := FALSE;")
            body.append("END_IF;")
            body.append(f"IF {plant_commands_enabled} THEN")
            body.append(f"    {cmd_valid} := {cmd};")
            body.append("ELSE")
            body.append(f"    {cmd_valid} := FALSE;")
            body.append("END_IF;")
            body.append(f"{permissive_ok} := {permissive};")
            body.append(f"{fault_active} := {fault};")
            body.append(f"{auto_active} := {auto_mode};")
            body.append(f"{run_feedback_active} := {run_feedback};")
            body.append(f"IF {fault_active} THEN")
            body.append(f"    {run_cmd} := FALSE;")
            body.append(f"    {status} := FALSE;")
            body.append(f"ELSIF {auto_active} THEN")
            body.append(f"    IF {permissive_ok} THEN")
            body.append(f"        IF {cmd_valid} THEN")
            body.append(f"            {run_cmd} := TRUE;")
            body.append(f"            IF {run_feedback_active} THEN")
            body.append(f"                {status} := TRUE;")
            body.append("            ELSE")
            body.append(f"                {status} := {run_cmd};")
            body.append("            END_IF;")
            body.append("        ELSE")
            body.append(f"            {run_cmd} := FALSE;")
            body.append(f"            {status} := FALSE;")
            body.append("        END_IF;")
            body.append("    ELSE")
            body.append(f"        {run_cmd} := FALSE;")
            body.append(f"        {status} := FALSE;")
            body.append("    END_IF;")
            body.append("ELSE")
            body.append(f"    {run_cmd} := FALSE;")
            body.append(f"    {status} := FALSE;")
            body.append("END_IF;")

        block_name = f"FB_EQ_{self._block_suffix(eq_tag)}"
        return self._render_function_block(block_name, symbol_types, external_symbols, body, local_vars)

    def _render_loop_file(self, loop, symbol_types: dict[str, str], *, write_output: bool = True) -> str:
        pv = self._symbol(loop.pv_tag or loop.sensor_tag)
        sp = self._symbol(loop.sp_tag or loop.setpoint_tag or st_codegen_utils.normalize_tag_with_suffix(loop.sensor_tag, "SP"))
        out = self._symbol(loop.output_tag_analog or loop.output_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "OUT"))
        mode = self._symbol(loop.mode_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "AUTO"))
        enable = self._symbol(loop.enable_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "ENABLE"))

        external_symbols = {pv, sp, out, mode, enable}
        body: list[str] = []
        local_vars: list[str] = []

        out_min = loop.output_min if loop.output_min is not None else 0.0
        out_max = loop.output_max if loop.output_max is not None else 100.0

        loop_name = self._block_suffix(loop.loop_tag)
        local_vars = [
            "    ERROR : REAL := 0.0;",
            "    P_TERM : REAL := 0.0;",
            "    I_TERM : REAL := 0.0;",
            "    D_TERM : REAL := 0.0;",
            "    PREV_ERROR : REAL := 0.0;",
            "    INTEGRAL : REAL := 0.0;",
            f"    KP_{loop_name} : REAL := 1.0;",
            f"    KI_{loop_name} : REAL := 0.1;",
            f"    KD_{loop_name} : REAL := 0.01;",
            f"    DT_{loop_name} : REAL := 1.0;",
            f"    LOOP_OUTPUT_UNCLAMPED_{loop_name} : REAL := 0.0;",
            f"    LOOP_OUTPUT_CLAMPED_{loop_name} : REAL := 0.0;",
        ]
        body.append(f"IF {enable} AND {mode} THEN")
        body.append(f"    ERROR := {sp} - {pv};")
        body.append(f"    P_TERM := KP_{loop_name} * ERROR;")
        body.append(f"    INTEGRAL := INTEGRAL + (ERROR * KI_{loop_name} * DT_{loop_name});")
        body.append("    I_TERM := INTEGRAL;")
        body.append(f"    D_TERM := KD_{loop_name} * (ERROR - PREV_ERROR) / DT_{loop_name};")
        body.append(f"    LOOP_OUTPUT_UNCLAMPED_{loop_name} := P_TERM + I_TERM + D_TERM;")
        body.append(f"    LOOP_OUTPUT_CLAMPED_{loop_name} := CLX_ClampReal(LOOP_OUTPUT_UNCLAMPED_{loop_name}, {out_min:.1f}, {out_max:.1f});")
        if write_output:
            body.append(f"    {out} := LOOP_OUTPUT_CLAMPED_{loop_name};")
        body.append("    PREV_ERROR := ERROR;")
        body.append("END_IF;")

        block_name = f"FB_LOOP_{self._block_suffix(loop.loop_tag)}"
        return self._render_function_block(block_name, symbol_types, external_symbols, body, local_vars)

    def _render_interlock_file(self, interlock, symbol_types: dict[str, str]) -> str:
        source = self._symbol(interlock.source_tag)
        target_cmd = self._symbol(interlock.target_command_tag or st_codegen_utils.normalize_tag_with_suffix(interlock.target_tag, "CMD"))
        target_out = self._symbol(interlock.target_output_tag) if interlock.target_output_tag else None
        inhibit_tag = self._symbol(interlock.inhibit_tag) if interlock.inhibit_tag else None

        source_signal = st_codegen_utils.infer_signal_type(interlock.source_tag, interlock.source_type)
        comparator = interlock.comparator or (">=" if source_signal == "analog" else "==")
        action_type = interlock.interlock_action_type or ("force_output" if target_out else "force_command")
        if action_type == "force_output" and target_out and target_cmd:
            action_type = "force_command"

        external_symbols = {source}
        if action_type in {"force_command", "disable_loop"}:
            external_symbols.add(target_cmd)
        if action_type == "force_output" and target_out:
            external_symbols.add(target_out)
        if action_type == "disable_loop" and inhibit_tag:
            external_symbols.add(inhibit_tag)

        threshold = interlock.threshold_tag
        if source_signal == "analog":
            threshold_symbol = self._symbol(threshold or st_codegen_utils.infer_threshold_tags(interlock.source_tag).get("INTERLOCK", "GENERIC_SP"))
            external_symbols.add(threshold_symbol)
            condition = f"{source} {comparator} {threshold_symbol}"
        else:
            rhs = "TRUE" if (threshold or "TRUE").upper() != "FALSE" else "FALSE"
            condition = f"{source} = {rhs}"

        safe_value = interlock.safe_value or ("0.0" if action_type == "force_output" else "FALSE")
        local_vars = ["    INTERLOCK_ACTIVE : BOOL := FALSE;"]
        body = [f"INTERLOCK_ACTIVE := {condition};", "IF INTERLOCK_ACTIVE THEN"]
        if action_type == "disable_loop" and inhibit_tag:
            body.append(f"    {inhibit_tag} := FALSE;")
        elif action_type == "force_output" and target_out:
            body.append(f"    {target_out} := {self._coerce_real_literal(safe_value, default=0.0)};")
        else:
            target_type = symbol_types.get(target_cmd, "BOOL")
            rendered = self._coerce_bool_literal(safe_value, default="FALSE") if target_type == "BOOL" else self._coerce_real_literal(safe_value, default=0.0)
            body.append(f"    {target_cmd} := {rendered};")
        body.append("END_IF;")

        block_name = f"FB_INTERLOCK_{self._block_suffix(interlock.interlock_id)}"
        return self._render_function_block(block_name, symbol_types, external_symbols, body, local_vars)

    def _render_alarm_group_file(self, group, symbol_types: dict[str, str]) -> str:
        external_symbols: set[str] = set()
        body: list[str] = []
        local_vars: list[str] = []
        seen_alarm_keys: set[tuple[str, str, str, str, str]] = set()

        for alarm in group.alarm_rules:
            dedupe_key = (
                alarm.source_tag,
                alarm.alarm_tag,
                alarm.alarm_type,
                alarm.comparator,
                str(alarm.threshold_tag or ""),
            )
            if dedupe_key in seen_alarm_keys:
                continue
            seen_alarm_keys.add(dedupe_key)

            source = self._symbol(alarm.source_tag)
            alarm_tag = self._symbol(alarm.alarm_tag)
            source_signal = st_codegen_utils.infer_signal_type(alarm.source_tag, alarm.source_type)

            external_symbols.add(source)
            external_symbols.add(alarm_tag)

            suffix = self._block_suffix(alarm.alarm_tag)
            threshold_exceeded = f"THRESHOLD_EXCEEDED_{suffix}"
            local_vars.append(f"    {threshold_exceeded} : BOOL := FALSE;")

            if alarm.alarm_type == "FAULT":
                body.append(f"{threshold_exceeded} := {source} = TRUE;")
                body.append(f"IF {threshold_exceeded} THEN")
                body.append(f"    {alarm_tag} := TRUE;")
                body.append("ELSE")
                body.append(f"    {alarm_tag} := FALSE;")
                body.append("END_IF;")
                continue

            if source_signal == "analog":
                threshold = self._symbol(alarm.threshold_tag or st_codegen_utils.infer_threshold_tags(alarm.source_tag).get(alarm.alarm_type, "GENERIC_SP"))
                external_symbols.add(threshold)
                body.append(f"{threshold_exceeded} := {source} {alarm.comparator} {threshold};")
            else:
                body.append(f"{threshold_exceeded} := {source} = TRUE;")

            body.append(f"IF {threshold_exceeded} THEN")
            body.append(f"    {alarm_tag} := TRUE;")
            body.append("ELSE")
            body.append(f"    {alarm_tag} := FALSE;")
            body.append("END_IF;")

        block_name = f"FB_ALARM_{self._block_suffix(group.group_name)}"
        return self._render_function_block(block_name, symbol_types, external_symbols, body, local_vars)

    def _render_sequence_file(self, sequence_name: str, steps: list, symbol_types: dict[str, str], execute_tag: str) -> str:
        external_symbols = {execute_tag, "CURRENT_PLANT_STATE"}

        for step in steps:
            if step.trigger_tag:
                symbol = self._symbol(step.trigger_tag)
                external_symbols.add(symbol)
            if step.transition_tag and step.transition_tag != "EXECUTE_RESET":
                symbol = self._symbol(step.transition_tag)
                external_symbols.add(symbol)
            if step.command_tag:
                external_symbols.add(self._symbol(step.command_tag))

        ordered_steps = sorted(
            ((step.expected_state or step.step_number), step) for step in steps
        )
        first_step = ordered_steps[0][0] if ordered_steps else 10

        edge_instance = "StartEdge" if sequence_name == "startup" else "StopEdge"
        local_vars: list[str] = ["    StepState : INT := 0;", f"    {edge_instance} : FB_R_TRIG;"]

        required_state = "PLANT_STARTING" if sequence_name == "startup" else "PLANT_STOPPING"
        body: list[str] = [f"{edge_instance}(CLK := {execute_tag});"]

        body.extend([
            f"IF CURRENT_PLANT_STATE <> {required_state} THEN",
            "    StepState := 0;",
            f"ELSIF NOT {execute_tag} THEN",
            "    StepState := 0;",
            "ELSE",
            "    CASE StepState OF",
            "        0:",
            f"            IF {edge_instance}.Q THEN",
            f"                StepState := {first_step};",
            "            END_IF;",
        ])

        for idx, (state, step) in enumerate(ordered_steps):
            next_state = ordered_steps[idx + 1][0] if idx + 1 < len(ordered_steps) else 0
            transition = self._symbol(step.transition_tag) if step.transition_tag and step.transition_tag != "EXECUTE_RESET" else (self._symbol(step.trigger_tag) if step.trigger_tag else "FALSE")
            body.append(f"        {state}:")
            if step.command_tag:
                command_symbol = self._symbol(step.command_tag)
                command_value = self._sequence_command_value(sequence_name, step, command_symbol)
                body.append(f"            {command_symbol} := {command_value};")
            if transition != "FALSE":
                body.append(f"            IF {transition} THEN")
                body.append(f"                StepState := {next_state};")
                body.append("            END_IF;")

        body.extend(
            [
                "        ELSE",
                "            StepState := 0;",
                "    END_CASE;",
                "END_IF;",
            ]
        )

        block_name = "FB_STARTUP_SEQUENCE" if sequence_name == "startup" else "FB_SHUTDOWN_SEQUENCE"
        return self._render_function_block(block_name, symbol_types, external_symbols, body, local_vars)

    @staticmethod
    def _sequence_command_value(sequence_name: str, step, command_symbol: str) -> str:
        if command_symbol == "PROCESS_STOPPED":
            return "TRUE"
        if command_symbol == "PROCESS_RUNNING":
            return "TRUE"
        if sequence_name != "shutdown":
            return "TRUE"
        description = (step.description or "").lower()
        if any(keyword in description for keyword in {"stop", "shutdown", "close", "disable", "de-energ"}):
            return "FALSE"
        if command_symbol.endswith("_ENABLE") or command_symbol.endswith("_CMD"):
            return "FALSE"
        return "TRUE"

    def _render_main(
        self,
        equipment_blocks: list[str],
        loop_blocks: list[str],
        interlock_blocks: list[str],
        alarm_blocks: list[str],
        sequence_blocks: list[str],
        system_blocks: list[str],
        include_startup: bool,
        include_shutdown: bool,
    ) -> str:
        self._validate_module_order(["interlocks", "sequences", "equipment", "loops", "alarms"])

        lines = ["PROGRAM Main", "VAR"]

        lines.append("    (* system supervisors first *)")
        for block in system_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"    INST_{suffix} : {block};")

        lines.append("    (* interlocks first *)")
        for block in interlock_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"    INST_{suffix} : {block};")

        lines.append("    (* sequences second *)")
        for block in sequence_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"    INST_{suffix} : {block};")

        lines.append("    (* equipment third *)")
        for block in equipment_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"    INST_{suffix} : {block};")

        lines.append("    (* loops fourth *)")
        for block in loop_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"    INST_{suffix} : {block};")

        lines.append("    (* alarms last *)")
        for block in alarm_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"    INST_{suffix} : {block};")
        lines.append("END_VAR")

        lines.extend(
            [
                "VAR_EXTERNAL",
                "    STARTUP_CMD : BOOL;",
                "    SHUTDOWN_CMD : BOOL;",
                "    PLANT_START_CMD : BOOL;",
                "    PLANT_STOP_CMD : BOOL;",
                "END_VAR",
                "",
            ]
        )

        lines.append("PLANT_START_CMD := STARTUP_CMD;")
        lines.append("PLANT_STOP_CMD := SHUTDOWN_CMD;")

        lines.append("(* system supervisors first *)")
        for block in system_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"INST_{suffix}();")

        lines.append("(* interlocks first *)")
        for block in interlock_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"INST_{suffix}();")

        lines.append("(* sequences second *)")
        for block in sequence_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"INST_{suffix}();")

        lines.append("(* equipment third *)")
        for block in equipment_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"INST_{suffix}();")

        lines.append("(* loops fourth *)")
        for block in loop_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"INST_{suffix}();")

        lines.append("(* alarms last *)")
        for block in alarm_blocks:
            suffix = block.replace("FB_", "")
            lines.append(f"INST_{suffix}();")

        lines.append("END_PROGRAM")
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _reserved_tokens() -> set[str]:
        return {
            "IF",
            "THEN",
            "ELSE",
            "ELSIF",
            "END_IF",
            "CASE",
            "OF",
            "END_CASE",
            "TRUE",
            "FALSE",
            "AND",
            "OR",
            "NOT",
            "FUNCTION_BLOCK",
            "FUNCTION",
            "TYPE",
            "END_TYPE",
            "VAR",
            "VAR_GLOBAL",
            "VAR_INPUT",
            "VAR_OUTPUT",
            "VAR_EXTERNAL",
            "VAR_IN_OUT",
            "VAR_TEMP",
            "END_VAR",
            "REAL",
            "BOOL",
            "INT",
            "END_FUNCTION_BLOCK",
            "END_FUNCTION",
            "PROGRAM",
            "END_PROGRAM",
            "CLX_CLAMPREAL",
            "FB_R_TRIG",
            "PLANT_STATE",
            "PLANT_STOPPED",
            "PLANT_STARTING",
            "PLANT_RUNNING",
            "PLANT_STOPPING",
            "PLANT_FAULT",
        }

    def _normalize_symbol_integrity(
        self,
        relative_path: str,
        content: str,
        symbol_types: dict[str, str],
    ) -> str:
        lines = content.splitlines()
        sections: list[dict] = []
        declared: dict[str, dict] = {}
        reserved = self._reserved_tokens()

        in_var = False
        current_section: dict | None = None
        for idx, line in enumerate(lines):
            stripped = line.strip().upper()
            if stripped in {"VAR", "VAR_GLOBAL", "VAR_INPUT", "VAR_OUTPUT", "VAR_EXTERNAL", "VAR_IN_OUT", "VAR_TEMP"}:
                in_var = True
                current_section = {"type": stripped, "start": idx, "end": None}
                sections.append(current_section)
                continue
            if in_var and stripped == "END_VAR":
                in_var = False
                if current_section is not None:
                    current_section["end"] = idx
                current_section = None
                continue
            if in_var:
                match = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*:\s*([A-Z_][A-Z0-9_]*)", line, flags=re.IGNORECASE)
                if match:
                    name = match.group(1).upper()
                    declared[name] = {"line": idx, "type": match.group(2).upper(), "section": current_section["type"] if current_section else "VAR"}

        executable_lines = []
        in_var = False
        for line in lines:
            stripped = line.strip().upper()
            if stripped in {"VAR", "VAR_GLOBAL", "VAR_INPUT", "VAR_OUTPUT", "VAR_EXTERNAL", "VAR_IN_OUT", "VAR_TEMP"}:
                in_var = True
                continue
            if in_var and stripped == "END_VAR":
                in_var = False
                continue
            if not in_var:
                executable_lines.append(line)

        used = set(re.findall(r"\b[A-Z_][A-Z0-9_]*\b", "\n".join(executable_lines).upper()))
        used = {token for token in used if token not in reserved and not token.startswith("FB_") and not token.startswith("INST_")}

        missing = sorted(token for token in used if token not in declared)
        if missing and sections:
            target = next((section for section in sections if section["type"] == "VAR_EXTERNAL"), None)
            if target is None:
                target = sections[0]
            insert_idx = target["end"]
            for symbol in missing:
                declared_type = symbol_types.get(symbol, st_codegen_utils.infer_st_type(symbol))
                lines.insert(insert_idx, f"    {symbol} : {declared_type};")
                insert_idx += 1
                for section in sections:
                    if section["end"] is not None and section["end"] >= target["end"]:
                        section["end"] += 1

        required_keep = {
            "CURRENT_PLANT_STATE",
            "NEXT_PLANT_STATE",
            "PLANT_START_CMD",
            "PLANT_STOP_CMD",
            "PLANT_FAULT_ACTIVE",
            "PROCESS_RUNNING",
            "PROCESS_STOPPED",
            "STARTUP_CMD",
            "SHUTDOWN_CMD",
        }
        remove_indices: set[int] = set()
        for name, meta in declared.items():
            if name not in used and name not in required_keep and meta["section"] in {"VAR", "VAR_EXTERNAL", "VAR_GLOBAL"}:
                remove_indices.add(meta["line"])
        if remove_indices:
            lines = [line for idx, line in enumerate(lines) if idx not in remove_indices]

        return "\n".join(lines).strip() + "\n"

    def _ensure_shutdown_completion_flag(self, content: str) -> str:
        if "PROCESS_STOPPED := TRUE;" in content.upper():
            return content
        marker = "END_CASE;"
        if marker in content:
            return content.replace(marker, "        PROCESS_STOPPED := TRUE;\n" + marker)
        return content

    def _run_deterministic_integrity_pass(
        self,
        model: CompletedLogicModel,
        generated_contents: dict[str, str],
        symbol_types: dict[str, str],
    ) -> None:
        if "system/system_state_manager.st" in generated_contents:
            state_content = generated_contents["system/system_state_manager.st"].upper()
            if "NEXT_PLANT_STATE := CURRENT_PLANT_STATE;" not in state_content:
                raise ValueError("Deterministic integrity failed: state manager missing default NEXT state initialization")
            if "STARTEDGE(CLK := PLANT_START_CMD);" not in state_content or "STOPEDGE(CLK := PLANT_STOP_CMD);" not in state_content:
                raise ValueError("Deterministic integrity failed: state manager missing edge trigger initialization")

        shutdown_path = "sequences/shutdown_sequence.st"
        if shutdown_path in generated_contents:
            generated_contents[shutdown_path] = self._ensure_shutdown_completion_flag(generated_contents[shutdown_path])

        for path, content in list(generated_contents.items()):
            generated_contents[path] = self._normalize_symbol_integrity(path, content, symbol_types)

        for path, content in generated_contents.items():
            upper = content.upper()
            if path.startswith("sequences/startup") and "IF CURRENT_PLANT_STATE <> PLANT_STARTING THEN" not in upper:
                raise ValueError("Deterministic integrity failed: startup sequence missing plant-state guard")
            if path.startswith("sequences/shutdown") and "IF CURRENT_PLANT_STATE <> PLANT_STOPPING THEN" not in upper:
                raise ValueError("Deterministic integrity failed: shutdown sequence missing plant-state guard")
            if path.startswith("sequences/") and ("STARTEDGE" in upper or "STOPEDGE" in upper):
                if "FB_R_TRIG" not in upper:
                    raise ValueError(f"Deterministic integrity failed: {path} missing FB_R_TRIG declaration")
            if path.startswith("control_loops/") and "CLX_CLAMPREAL(" not in upper:
                raise ValueError(f"Deterministic integrity failed: {path} missing PID output clamp")
            if path.startswith("equipment/") and "PLANT_COMMANDS_ENABLED" not in upper:
                raise ValueError(f"Deterministic integrity failed: {path} missing plant command gating")

        main_upper = generated_contents.get("main.st", "").upper()
        order_markers = [
            "(* SYSTEM SUPERVISORS FIRST *)",
            "(* INTERLOCKS FIRST *)",
            "(* SEQUENCES SECOND *)",
            "(* EQUIPMENT THIRD *)",
            "(* LOOPS FOURTH *)",
            "(* ALARMS LAST *)",
        ]
        positions = [main_upper.find(marker) for marker in order_markers]
        if any(position == -1 for position in positions) or positions != sorted(positions):
            raise ValueError("Deterministic integrity failed: execution layer order is not fixed")

    @classmethod
    def _validate_module_order(cls, module_order: list[str]) -> None:
        if module_order != cls.REQUIRED_MODULE_ORDER:
            raise ValueError(
                f"Invalid module order: {module_order}. Required order is {cls.REQUIRED_MODULE_ORDER}."
            )

    @staticmethod
    def _render_utilities() -> str:
        return "\n".join(
            [
                "FUNCTION CLX_ClampReal : REAL",
                "VAR_INPUT",
                "    Value : REAL;",
                "    MinValue : REAL;",
                "    MaxValue : REAL;",
                "END_VAR",
                "IF Value < MinValue THEN",
                "    CLX_ClampReal := MinValue;",
                "ELSIF Value > MaxValue THEN",
                "    CLX_ClampReal := MaxValue;",
                "ELSE",
                "    CLX_ClampReal := Value;",
                "END_IF;",
                "END_FUNCTION",
                "",
            ]
        )

    @staticmethod
    def _render_r_trig_utility() -> str:
        return "\n".join(
            [
                "FUNCTION_BLOCK FB_R_TRIG",
                "VAR_INPUT",
                "    CLK : BOOL;",
                "END_VAR",
                "VAR_OUTPUT",
                "    Q : BOOL;",
                "END_VAR",
                "VAR",
                "    MEM : BOOL := FALSE;",
                "END_VAR",
                "Q := CLK AND NOT MEM;",
                "MEM := CLK;",
                "END_FUNCTION_BLOCK",
                "",
            ]
        )

    @staticmethod
    def _render_system_state_manager() -> str:
        return "\n".join(
            [
                "TYPE PLANT_STATE : (PLANT_STOPPED, PLANT_STARTING, PLANT_RUNNING, PLANT_STOPPING, PLANT_FAULT); END_TYPE",
                "",
                "VAR_GLOBAL",
                "    CURRENT_PLANT_STATE : PLANT_STATE := PLANT_STOPPED;",
                "    NEXT_PLANT_STATE : PLANT_STATE := PLANT_STOPPED;",
                "    PLANT_START_CMD : BOOL;",
                "    PLANT_STOP_CMD : BOOL;",
                "    PLANT_FAULT_ACTIVE : BOOL;",
                "    PROCESS_RUNNING : BOOL;",
                "    PROCESS_STOPPED : BOOL;",
                "END_VAR",
                "",
                "FUNCTION_BLOCK FB_SYSTEM_STATE_MANAGER",
                "VAR",
                "    StartEdge : FB_R_TRIG;",
                "    StopEdge : FB_R_TRIG;",
                "END_VAR",
                "",
                "StartEdge(CLK := PLANT_START_CMD);",
                "StopEdge(CLK := PLANT_STOP_CMD);",
                "NEXT_PLANT_STATE := CURRENT_PLANT_STATE;",
                "",
                "CASE CURRENT_PLANT_STATE OF",
                "    PLANT_STOPPED:",
                "        IF StartEdge.Q THEN",
                "            NEXT_PLANT_STATE := PLANT_STARTING;",
                "        END_IF;",
                "    PLANT_STARTING:",
                "        IF PROCESS_RUNNING THEN",
                "            NEXT_PLANT_STATE := PLANT_RUNNING;",
                "        END_IF;",
                "        IF PLANT_FAULT_ACTIVE THEN",
                "            NEXT_PLANT_STATE := PLANT_FAULT;",
                "        END_IF;",
                "    PLANT_RUNNING:",
                "        IF StopEdge.Q THEN",
                "            NEXT_PLANT_STATE := PLANT_STOPPING;",
                "        END_IF;",
                "        IF PLANT_FAULT_ACTIVE THEN",
                "            NEXT_PLANT_STATE := PLANT_FAULT;",
                "        END_IF;",
                "    PLANT_STOPPING:",
                "        IF PROCESS_STOPPED THEN",
                "            NEXT_PLANT_STATE := PLANT_STOPPED;",
                "        END_IF;",
                "    PLANT_FAULT:",
                "        IF NOT PLANT_FAULT_ACTIVE THEN",
                "            NEXT_PLANT_STATE := PLANT_STOPPED;",
                "        END_IF;",
                "END_CASE;",
                "CURRENT_PLANT_STATE := NEXT_PLANT_STATE;",
                "END_FUNCTION_BLOCK",
                "",
            ]
        )

    def _render_system_fault_manager(self, model: CompletedLogicModel) -> str:
        fault_alarm_tags = sorted(
            {
                self._symbol(alarm.alarm_tag)
                for group in model.alarm_groups
                for alarm in group.alarm_rules
                if alarm.alarm_type == "FAULT"
            }
        )
        lines = [
            "FUNCTION_BLOCK FB_SYSTEM_FAULT_MANAGER",
            "VAR_EXTERNAL",
            "    PLANT_FAULT_ACTIVE : BOOL;",
        ]
        for tag in fault_alarm_tags:
            lines.append(f"    {tag} : BOOL;")
        lines.extend(
            [
                "END_VAR",
                "",
                "PLANT_FAULT_ACTIVE := FALSE;",
            ]
        )
        for tag in fault_alarm_tags:
            lines.extend(
                [
                    f"IF {tag} THEN",
                    "    PLANT_FAULT_ACTIVE := TRUE;",
                    "END_IF;",
                ]
            )
        lines.extend(["END_FUNCTION_BLOCK", ""])
        return "\n".join(lines)

    @staticmethod
    def _logic_expansion_pass(content: str) -> str:
        return content

    @staticmethod
    def _ensure_no_inline_boolean_expressions(relative_path: str, content: str) -> None:
        assignment_pattern = re.compile(r"^\s*[A-Z_][A-Z0-9_]*\s*:=\s*[^;]*\b(AND|OR)\b[^;]*;\s*$", re.IGNORECASE)
        for line in content.splitlines():
            if assignment_pattern.match(line):
                raise ValueError(
                    f"Generation rule violation in {relative_path}: inline boolean expression detected ({line.strip()})."
                )

    def _run_production_completeness_layer(
        self,
        model: CompletedLogicModel,
        generated_contents: dict[str, str],
    ) -> None:
        errors: list[str] = []

        for relative_path, content in generated_contents.items():
            if not relative_path.endswith(".st"):
                continue
            declared: set[str] = set()
            executable_lines: list[str] = []
            in_var_block = False
            for line in content.splitlines():
                stripped = line.strip().upper()
                if stripped in {"VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_EXTERNAL", "VAR_IN_OUT", "VAR_TEMP", "VAR_GLOBAL"}:
                    in_var_block = True
                    continue
                if in_var_block and stripped == "END_VAR":
                    in_var_block = False
                    continue
                if in_var_block:
                    match = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*:\s*", line)
                    if match:
                        declared.add(match.group(1))
                else:
                    executable_lines.append(line)

            used = set(re.findall(r"\b[A-Z_][A-Z0-9_]*\b", "\n".join(executable_lines)))
            reserved = self._reserved_tokens()
            candidates = {
                token
                for token in used
                if "_" in token and token not in reserved and not token.startswith("FB_") and not token.startswith("INST_")
            }
            missing = sorted(token for token in candidates if token not in declared)
            if missing:
                errors.append(f"{relative_path}: missing declarations for {', '.join(missing[:8])}")

        pid_loop_paths = [path for path in generated_contents if path.startswith("control_loops/")]
        for path in pid_loop_paths:
            content = generated_contents[path].upper()
            if "INTEGRAL" not in content or "PREV_ERROR" not in content or "D_TERM" not in content:
                errors.append(f"{path}: loop is not full PID structure")

        sequence_paths = [path for path in generated_contents if path.startswith("sequences/")]
        for path in sequence_paths:
            content = generated_contents[path].upper()
            if "FB_R_TRIG" not in content or ".Q" not in content:
                errors.append(f"{path}: sequence missing start-edge detection")

        main_content = generated_contents.get("main.st", "")
        if "INST_SYSTEM_FAULT_MANAGER();" not in main_content or "INST_SYSTEM_STATE_MANAGER();" not in main_content:
            errors.append("main.st: missing system supervisor manager calls")
        call_lines = [line.strip() for line in main_content.splitlines() if line.strip().startswith("INST_") and line.strip().endswith("();")]
        first_interlock_call = next((idx for idx, line in enumerate(call_lines) if line.startswith("INST_INTERLOCK")), None)
        first_system_call = next((idx for idx, line in enumerate(call_lines) if line.startswith("INST_SYSTEM_")), None)
        if first_interlock_call is not None and first_system_call is not None and first_system_call > first_interlock_call:
            errors.append("main.st: system supervisors must execute before interlocks")
        interlock_call = main_content.find("(* interlocks first *)")
        equipment_call = main_content.find("(* equipment third *)")
        if interlock_call == -1 or equipment_call == -1 or interlock_call > equipment_call:
            errors.append("main.st: interlocks do not execute before equipment")

        sequence_content = "\n".join(generated_contents.get(path, "") for path in sequence_paths).upper()
        for routine in model.equipment_routines:
            if routine.command_tag:
                command_symbol = self._symbol(routine.command_tag)
                if command_symbol not in sequence_content:
                    errors.append(f"sequence command origin missing for {command_symbol}")

        if "system/system_state_manager.st" not in generated_contents:
            errors.append("missing system/system_state_manager.st")
        if "system/system_fault_manager.st" not in generated_contents:
            errors.append("missing system/system_fault_manager.st")

        fault_content = generated_contents.get("system/system_fault_manager.st", "").upper()
        if fault_content and "PLANT_FAULT_ACTIVE := FALSE;" not in fault_content:
            errors.append("system/system_fault_manager.st: missing per-scan fault reset")

        if errors:
            raise ValueError("Production completeness layer failed: " + " | ".join(errors))

    def generate(self, project_id: str, model: CompletedLogicModel) -> STGenerationResult:
        paths = project_service.workspace_paths(project_id)
        control_logic_root = paths.control_logic
        if control_logic_root.exists():
            for old_file in control_logic_root.rglob("*.st"):
                old_file.unlink(missing_ok=True)
        symbol_types = self._collect_symbol_types(model)

        files: list[GeneratedSTFile] = []
        generated_contents: dict[str, str] = {}
        equipment_blocks: list[str] = []
        loop_blocks: list[str] = []
        interlock_blocks: list[str] = []
        alarm_blocks: list[str] = []
        sequence_blocks: list[str] = []
        system_blocks: list[str] = ["FB_SYSTEM_FAULT_MANAGER", "FB_SYSTEM_STATE_MANAGER"]

        self._validate_module_order(["interlocks", "sequences", "equipment", "loops", "alarms"])

        for routine in sorted(model.equipment_routines, key=lambda item: item.equipment_tag):
            content = self._logic_expansion_pass(self._render_equipment_file(routine, symbol_types))
            stem = self._file_stem(routine.equipment_tag)
            relative = f"equipment/{stem}.st"
            self._ensure_no_inline_boolean_expressions(relative, content)
            generated_contents[relative] = content
            equipment_blocks.append(f"FB_EQ_{self._block_suffix(routine.equipment_tag)}")

        output_writer_owner: dict[str, str] = {}
        for loop in sorted(model.loops, key=lambda item: item.loop_tag):
            out_symbol = self._symbol(loop.output_tag_analog or loop.output_tag or st_codegen_utils.normalize_tag_with_suffix(loop.actuator_tag, "OUT"))
            write_output = False
            if loop.auto_owner == "loop_manager":
                current_owner = output_writer_owner.get(out_symbol)
                if current_owner is None:
                    output_writer_owner[out_symbol] = loop.loop_tag
                    write_output = True

            content = self._logic_expansion_pass(self._render_loop_file(loop, symbol_types, write_output=write_output))
            stem = self._file_stem(loop.loop_tag)
            relative = f"control_loops/{stem}.st"
            self._ensure_no_inline_boolean_expressions(relative, content)
            generated_contents[relative] = content
            loop_blocks.append(f"FB_LOOP_{self._block_suffix(loop.loop_tag)}")

        for interlock in sorted(model.interlocks, key=lambda item: item.interlock_id):
            content = self._logic_expansion_pass(self._render_interlock_file(interlock, symbol_types))
            stem = self._file_stem(interlock.interlock_id)
            relative = f"interlocks/{stem}.st"
            self._ensure_no_inline_boolean_expressions(relative, content)
            generated_contents[relative] = content
            interlock_blocks.append(f"FB_INTERLOCK_{self._block_suffix(interlock.interlock_id)}")

        for group in sorted(model.alarm_groups, key=lambda item: item.group_name):
            content = self._logic_expansion_pass(self._render_alarm_group_file(group, symbol_types))
            stem = self._file_stem(group.group_name)
            relative = f"alarms/{stem}.st"
            self._ensure_no_inline_boolean_expressions(relative, content)
            generated_contents[relative] = content
            alarm_blocks.append(f"FB_ALARM_{self._block_suffix(group.group_name)}")

        include_startup = bool(model.startup_sequence)
        include_shutdown = bool(model.shutdown_sequence)
        if include_startup:
            startup = self._logic_expansion_pass(self._render_sequence_file("startup", model.startup_sequence, symbol_types, "STARTUP_CMD"))
            self._ensure_no_inline_boolean_expressions("sequences/startup_sequence.st", startup)
            generated_contents["sequences/startup_sequence.st"] = startup
            sequence_blocks.append("FB_STARTUP_SEQUENCE")
        if include_shutdown:
            shutdown = self._logic_expansion_pass(self._render_sequence_file("shutdown", model.shutdown_sequence, symbol_types, "SHUTDOWN_CMD"))
            self._ensure_no_inline_boolean_expressions("sequences/shutdown_sequence.st", shutdown)
            generated_contents["sequences/shutdown_sequence.st"] = shutdown
            sequence_blocks.append("FB_SHUTDOWN_SEQUENCE")

        main_st = self._render_main(
            equipment_blocks=equipment_blocks,
            loop_blocks=loop_blocks,
            interlock_blocks=interlock_blocks,
            alarm_blocks=alarm_blocks,
            sequence_blocks=sequence_blocks,
            system_blocks=system_blocks,
            include_startup=include_startup,
            include_shutdown=include_shutdown,
        )
        main_st = self._logic_expansion_pass(main_st)
        self._ensure_no_inline_boolean_expressions("main.st", main_st)
        generated_contents["main.st"] = main_st
        utilities_st = self._logic_expansion_pass(self._render_utilities())
        generated_contents["utilities/utilities.st"] = utilities_st
        r_trig_st = self._logic_expansion_pass(self._render_r_trig_utility())
        generated_contents["utilities/r_trig.st"] = r_trig_st
        generated_contents["system/system_state_manager.st"] = self._logic_expansion_pass(self._render_system_state_manager())
        generated_contents["system/system_fault_manager.st"] = self._logic_expansion_pass(self._render_system_fault_manager(model))

        self._run_deterministic_integrity_pass(model, generated_contents, symbol_types)

        self._run_production_completeness_layer(model, generated_contents)

        for relative_path, content in sorted(generated_contents.items(), key=lambda item: item[0]):
            files.append(self._write_file(control_logic_root, relative_path, content))

        files = sorted(files, key=lambda item: item.relative_path)
        self.logger.info("ST generation completed: project=%s files=%s", project_id, len(files))
        return STGenerationResult(project_id=project_id, output_root=str(control_logic_root), files=files)


st_generator = STGenerator()
