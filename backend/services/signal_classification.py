from __future__ import annotations

import re


_ANALOG_PREFIXES = (
    "LT",
    "LIT",
    "AIT",
    "AT",
    "FIT",
    "FT",
    "PIT",
    "PT",
    "TT",
    "TIT",
    "DPIT",
    "DPT",
)
_DIGITAL_PREFIXES = (
    "LS",
    "LSH",
    "LSHH",
    "LSL",
    "LSLL",
    "PS",
    "TS",
    "FS",
)
_ACTUATOR_PREFIXES = (
    "P",
    "PMP",
    "BL",
    "BLOW",
    "MTR",
    "M",
    "VAL",
    "XV",
    "CV",
    "FCV",
)
_PROCESS_NODE_TYPES = {"process_unit", "tank", "basin", "clarifier"}
_SENSOR_NODE_TYPES = {
    "flow_transmitter",
    "level_transmitter",
    "pressure_transmitter",
    "differential_pressure_transmitter",
    "temperature_transmitter",
    "analyzer",
    "level_switch",
}
_ACTUATOR_NODE_TYPES = {"pump", "valve", "control_valve", "blower", "chemical_system_device", "motor"}


def normalize_tag(tag: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", (tag or "").upper()).strip("_")


def _tag_prefix(tag: str) -> str:
    token = normalize_tag(tag)
    if "_" in token:
        return token.split("_")[0]
    letters = re.match(r"^[A-Z]+", token)
    return letters.group(0) if letters else token


def device_type_from_tag(tag: str, node_type: str | None = None) -> str:
    canonical = (node_type or "").strip().lower()
    if canonical:
        return canonical

    prefix = _tag_prefix(tag)
    if prefix.startswith(("P", "PMP")):
        return "pump"
    if prefix.startswith(("VAL", "XV", "CV", "FCV")):
        return "valve"
    if prefix.startswith(("TK", "TANK", "BAS", "CLR")):
        return "process_unit"
    if prefix.startswith(_ANALOG_PREFIXES):
        return "sensor"
    if prefix.startswith(_DIGITAL_PREFIXES):
        return "switch"
    return "equipment"


def signal_type_from_tag(tag: str, node_type: str | None = None) -> str:
    canonical = (node_type or "").strip().lower()
    if canonical in _PROCESS_NODE_TYPES:
        return "process"
    if canonical in _SENSOR_NODE_TYPES:
        if canonical == "level_switch":
            return "digital"
        return "analog"
    if canonical in _ACTUATOR_NODE_TYPES:
        return "digital"

    prefix = _tag_prefix(tag)
    if prefix.startswith(_ANALOG_PREFIXES):
        return "analog"
    if prefix.startswith(_DIGITAL_PREFIXES) or prefix.startswith(_ACTUATOR_PREFIXES):
        return "digital"
    return "unknown"


def process_role_from_node(node_type: str | None) -> str:
    canonical = (node_type or "").strip().lower()
    if canonical in _SENSOR_NODE_TYPES:
        return "sensor"
    if canonical in _ACTUATOR_NODE_TYPES:
        return "actuator"
    if canonical in _PROCESS_NODE_TYPES:
        return "process"
    return "equipment"


def classification_confidence(tag: str, node_type: str | None) -> float:
    canonical = (node_type or "").strip().lower()
    prefix = _tag_prefix(tag)
    if canonical in _SENSOR_NODE_TYPES | _ACTUATOR_NODE_TYPES | _PROCESS_NODE_TYPES:
        return 0.92
    if prefix.startswith(_ANALOG_PREFIXES) or prefix.startswith(_DIGITAL_PREFIXES) or prefix.startswith(_ACTUATOR_PREFIXES):
        return 0.82
    if canonical:
        return 0.75
    return 0.6


def controller_type_from_sensor(tag: str, node_type: str | None) -> str:
    canonical = (node_type or "").lower()
    prefix = _tag_prefix(tag)
    if canonical in {"analyzer", "pressure_transmitter", "flow_transmitter"} or prefix.startswith(("AIT", "PIT", "FIT", "FT", "PT")):
        return "PID"
    return "ON_OFF"
