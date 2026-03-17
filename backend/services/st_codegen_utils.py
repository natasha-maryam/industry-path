from __future__ import annotations

import re


class STCodegenUtils:
    """Shared helpers for ST-safe symbols and deterministic codegen inference."""

    _analog_prefixes = ("AIT", "LIT", "FIT", "PIT", "DPIT", "LT", "PT", "FT", "AT")
    _boolean_prefixes = ("LS", "PS", "ZS", "ESD", "HS", "MTR")
    _real_suffixes = (
        "_OUT",
        "_POSITION",
        "_POS",
        "_SPEED_REF",
        "_REF",
        "_SP",
        "_PV",
        "_HI_SP",
        "_HH_SP",
        "_LO_SP",
        "_LL_SP",
    )
    _bool_suffixes = (
        "_CMD",
        "_OPEN_CMD",
        "_CLOSE_CMD",
        "_ENABLE",
        "_EN",
        "_AUTO",
        "_MANUAL",
        "_STATUS",
        "_FAULT",
        "_PERMISSIVE",
        "_RUN_FB",
        "_RUN_CMD",
    )
    _int_suffixes = ("_STEP", "_STATE", "_MODE")

    @staticmethod
    def normalize_symbol(raw: str | None) -> str:
        if not raw:
            return "UNRESOLVED"
        symbol = raw.strip().upper().replace("-", "_").replace(" ", "_")
        symbol = re.sub(r"[^A-Z0-9_]", "_", symbol)
        symbol = re.sub(r"_+", "_", symbol).strip("_")
        if not symbol:
            symbol = "UNRESOLVED"
        if symbol[0].isdigit():
            symbol = f"X_{symbol}"
        return symbol

    def normalize_tag_with_suffix(self, base_tag: str | None, suffix: str) -> str:
        base = self.normalize_symbol(base_tag)
        suffix_symbol = self.normalize_symbol(suffix)
        return f"{base}_{suffix_symbol}"

    def infer_st_type(self, tag: str | None, canonical_type: str | None = None, role: str | None = None) -> str:
        normalized = self.normalize_symbol(tag)
        canonical = (canonical_type or "").lower()
        normalized_role = (role or "").lower()

        if normalized_role in {"sequence_state", "step_state", "state"}:
            return "INT"

        if canonical in {
            "flow_transmitter",
            "level_transmitter",
            "pressure_transmitter",
            "differential_pressure_transmitter",
            "analyzer",
        }:
            return "REAL"

        if canonical in {"level_switch"}:
            return "BOOL"
        if canonical in {"pump", "blower", "valve", "chemical_system_device"}:
            return "BOOL"
        if canonical in {"control_valve"}:
            if normalized.endswith(self._real_suffixes) or normalized_role in {"analog_output", "output_analog"}:
                return "REAL"
            return "BOOL"

        if normalized.endswith(self._int_suffixes):
            return "INT"
        if normalized.endswith(self._real_suffixes):
            return "REAL"
        if normalized.endswith(self._bool_suffixes):
            return "BOOL"

        if normalized.startswith(self._analog_prefixes):
            return "REAL"
        if normalized.startswith(self._boolean_prefixes):
            return "BOOL"

        return "BOOL"

    def infer_signal_type(self, tag: str | None, canonical_type: str | None = None) -> str:
        st_type = self.infer_st_type(tag, canonical_type)
        if st_type == "REAL":
            return "analog"
        if st_type == "BOOL":
            return "boolean"
        return "unknown"

    def is_real_signal(self, tag: str | None, canonical_type: str | None = None, role: str | None = None) -> bool:
        return self.infer_st_type(tag, canonical_type, role=role) == "REAL"

    def is_bool_signal(self, tag: str | None, canonical_type: str | None = None, role: str | None = None) -> bool:
        return self.infer_st_type(tag, canonical_type, role=role) == "BOOL"

    def infer_loop_output_tags(self, actuator_tag: str | None, actuator_type: str | None, control_strategy: str | None) -> tuple[str, str | None]:
        base = self.normalize_symbol(actuator_tag)
        strategy = (control_strategy or "").upper()
        actuator = (actuator_type or "").lower()
        is_modulating = strategy == "PID" or actuator == "control_valve"
        if is_modulating:
            return f"{base}_OUT", f"{base}_CMD"
        if actuator in {"pump", "blower", "chemical_system_device"}:
            return f"{base}_RUN_CMD", f"{base}_RUN_CMD"
        return f"{base}_CMD", f"{base}_CMD"

    def infer_equipment_signal_family(self, equipment_tag: str | None, canonical_type: str | None) -> dict[str, str | None]:
        base = self.normalize_symbol(equipment_tag)
        behavior = self.classify_equipment_behavior(canonical_type)

        command_tag = f"{base}_RUN_CMD" if behavior == "start_stop" else f"{base}_CMD"
        status_tag = f"{base}_RUN_STATUS" if behavior == "start_stop" else f"{base}_STATUS"
        return {
            "command_tag": command_tag,
            "status_tag": status_tag,
            "fault_tag": f"{base}_FAULT",
            "permissive_tag": f"{base}_PERMISSIVE",
            "auto_mode_tag": f"{base}_AUTO",
            "manual_mode_tag": f"{base}_MANUAL",
            "run_feedback_tag": f"{base}_RUN_FB",
            "open_command_tag": f"{base}_OPEN_CMD" if behavior == "open_close" else None,
            "close_command_tag": f"{base}_CLOSE_CMD" if behavior == "open_close" else None,
            "output_tag": f"{base}_OUT" if behavior == "modulating" else None,
            "run_command_tag": f"{base}_RUN_CMD",
            "run_status_tag": f"{base}_RUN_STATUS",
        }

    def infer_command_dependencies(self, command_tag: str | None) -> dict[str, list[str]] | None:
        normalized = self.normalize_symbol(command_tag)
        if not normalized or not normalized.endswith("_CMD"):
            return None

        if normalized in {"STARTUP_CMD", "SHUTDOWN_CMD", "STOP_ALL_CMD", "AUTO_ENABLE_CMD"} or normalized.startswith("PLANT_"):
            return None

        if normalized.endswith("_RUN_CMD"):
            base = normalized[: -len("_RUN_CMD")]
            return {
                "status_tags": [f"{base}_RUN_STATUS"],
                "fault_tags": [f"{base}_FAULT"],
            }

        if normalized.endswith("_START_CMD"):
            base = normalized[: -len("_START_CMD")]
            return {
                "status_tags": [f"{base}_RUN_STATUS"],
                "fault_tags": [f"{base}_FAULT"],
            }

        if normalized.endswith("_STOP_CMD"):
            base = normalized[: -len("_STOP_CMD")]
            return {
                "status_tags": [f"{base}_RUN_STATUS"],
                "fault_tags": [f"{base}_FAULT"],
            }

        if normalized.endswith("_OPEN_CMD"):
            base = normalized[: -len("_OPEN_CMD")]
            return {
                "status_tags": [f"{base}_STATUS"],
                "fault_tags": [f"{base}_FAULT"],
            }

        if normalized.endswith("_CLOSE_CMD"):
            base = normalized[: -len("_CLOSE_CMD")]
            return {
                "status_tags": [f"{base}_STATUS"],
                "fault_tags": [f"{base}_FAULT"],
            }

        base = normalized[: -len("_CMD")]
        return {
            "status_tags": [f"{base}_STATUS"],
            "fault_tags": [f"{base}_FAULT"],
        }

    def infer_threshold_tags(self, sensor_tag: str | None) -> dict[str, str]:
        base = self.normalize_symbol(sensor_tag)
        return {
            "HI": f"{base}_HI_SP",
            "HH": f"{base}_HH_SP",
            "LO": f"{base}_LO_SP",
            "LL": f"{base}_LL_SP",
            "INTERLOCK": f"{base}_HH_SP",
        }

    @staticmethod
    def classify_equipment_behavior(canonical_type: str | None) -> str:
        canonical = (canonical_type or "").lower()
        if canonical in {"pump", "blower", "chemical_system_device"}:
            return "start_stop"
        if canonical in {"control_valve"}:
            return "modulating"
        if canonical in {"valve"}:
            return "open_close"
        return "start_stop"


st_codegen_utils = STCodegenUtils()
