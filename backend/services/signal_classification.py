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
    "PCV",
    "TCV",
    "LCV",
    "VFD",
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
_ACTUATOR_NODE_TYPES = {"pump", "valve", "control_valve", "blower", "chemical_system_device", "motor", "vfd"}
_CONTROLLER_NODE_TYPES = {"panel"}
_BEHAVIORAL_SENSOR_PREFIXES = ("DPIT", "FIT", "LIT", "PIT", "TIT", "AIT", "FT", "LT", "PT", "TT", "AT")
_BEHAVIORAL_ACTUATOR_PREFIXES = ("FCV", "PCV", "TCV", "LCV", "XV", "CV", "VAL", "VFD", "PMP", "P", "BL", "BLOW", "MTR")
_BEHAVIORAL_CONTROLLER_PREFIXES = ("FIC", "LIC", "PIC", "TIC", "AIC", "UIC", "PLC", "PID", "CTRL")
_BEHAVIORAL_SENSOR_KEYWORDS = ("transmitter", "sensor", "analyzer", "switch", "indicator")
_BEHAVIORAL_ACTUATOR_KEYWORDS = ("valve", "pump", "blower", "vfd", "drive", "motor", "damper")
_BEHAVIORAL_CONTROLLER_KEYWORDS = ("controller", "pid", "plc", "control_panel", "loop_control", "control_station")
_BEHAVIORAL_PROCESS_KEYWORDS = ("basin", "tank", "reactor", "clarifier", "process_unit", "aeration_basin")


def normalize_tag(tag: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", (tag or "").upper()).strip("_")


def _tag_prefix(tag: str) -> str:
    token = normalize_tag(tag)
    if "_" in token:
        return token.split("_")[0]
    letters = re.match(r"^[A-Z]+", token)
    return letters.group(0) if letters else token


def _matches_keywords(value: str, keywords: tuple[str, ...]) -> bool:
    normalized = normalize_tag(value).replace("_", " ").lower()
    return any(keyword in normalized for keyword in keywords)


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
    if canonical in _CONTROLLER_NODE_TYPES:
        return "controller"
    if canonical in _ACTUATOR_NODE_TYPES:
        return "actuator"
    if canonical in _PROCESS_NODE_TYPES:
        return "process"
    return "equipment"


def classify_behavioral_role(
    tag: str,
    node_type: str | None = None,
    normalized_equipment: str | None = None,
    normalized_type: str | None = None,
) -> tuple[str, list[str], float]:
    role_scores: dict[str, float] = {}
    role_evidence: dict[str, list[str]] = {"sensor": [], "controller": [], "actuator": [], "process": []}

    def add_support(role: str, score: float, evidence: str) -> None:
        role_scores[role] = role_scores.get(role, 0.0) + score
        role_evidence[role].append(evidence)

    canonical_role = process_role_from_node(node_type)
    if canonical_role in role_evidence:
        add_support(canonical_role, 0.72, f"canonical_type:{(node_type or '').lower()}")

    prefix = _tag_prefix(tag)
    if any(prefix.startswith(item) for item in _BEHAVIORAL_SENSOR_PREFIXES):
        add_support("sensor", 0.58, f"tag_prefix:{prefix}")
    if any(prefix.startswith(item) for item in _BEHAVIORAL_CONTROLLER_PREFIXES):
        add_support("controller", 0.58, f"tag_prefix:{prefix}")
    if any(prefix.startswith(item) for item in _BEHAVIORAL_ACTUATOR_PREFIXES):
        add_support("actuator", 0.58, f"tag_prefix:{prefix}")

    if normalized_type and _matches_keywords(normalized_type, _BEHAVIORAL_SENSOR_KEYWORDS):
        add_support("sensor", 0.56, f"normalized_type:{normalize_tag(normalized_type).lower()}")
    if normalized_type and _matches_keywords(normalized_type, _BEHAVIORAL_CONTROLLER_KEYWORDS):
        add_support("controller", 0.56, f"normalized_type:{normalize_tag(normalized_type).lower()}")
    if normalized_type and _matches_keywords(normalized_type, _BEHAVIORAL_ACTUATOR_KEYWORDS):
        add_support("actuator", 0.56, f"normalized_type:{normalize_tag(normalized_type).lower()}")
    if normalized_type and _matches_keywords(normalized_type, _BEHAVIORAL_PROCESS_KEYWORDS):
        add_support("process", 0.56, f"normalized_type:{normalize_tag(normalized_type).lower()}")

    if normalized_equipment and _matches_keywords(normalized_equipment, _BEHAVIORAL_SENSOR_KEYWORDS):
        add_support("sensor", 0.54, f"normalized_equipment:{normalize_tag(normalized_equipment).lower()}")
    if normalized_equipment and _matches_keywords(normalized_equipment, _BEHAVIORAL_CONTROLLER_KEYWORDS):
        add_support("controller", 0.54, f"normalized_equipment:{normalize_tag(normalized_equipment).lower()}")
    if normalized_equipment and _matches_keywords(normalized_equipment, _BEHAVIORAL_ACTUATOR_KEYWORDS):
        add_support("actuator", 0.54, f"normalized_equipment:{normalize_tag(normalized_equipment).lower()}")
    if normalized_equipment and _matches_keywords(normalized_equipment, _BEHAVIORAL_PROCESS_KEYWORDS):
        add_support("process", 0.54, f"normalized_equipment:{normalize_tag(normalized_equipment).lower()}")

    if not role_scores:
        fallback = canonical_role if canonical_role != "equipment" else "equipment"
        return fallback, ([f"fallback:{fallback}"] if fallback != "equipment" else []), classification_confidence(tag, node_type)

    selected_role = max(
        role_scores,
        key=lambda role: (role_scores[role], len(role_evidence[role]), role == canonical_role),
    )
    confidence = min(0.98, 0.62 + min(role_scores[selected_role], 1.4) * 0.18 + (0.05 if len(role_evidence[selected_role]) > 1 else 0.0))
    return selected_role, sorted(set(role_evidence[selected_role])), round(confidence, 3)


def classification_confidence(tag: str, node_type: str | None) -> float:
    canonical = (node_type or "").strip().lower()
    prefix = _tag_prefix(tag)
    if canonical in _SENSOR_NODE_TYPES | _CONTROLLER_NODE_TYPES | _ACTUATOR_NODE_TYPES | _PROCESS_NODE_TYPES:
        return 0.92
    if prefix.startswith(_ANALOG_PREFIXES) or prefix.startswith(_DIGITAL_PREFIXES) or prefix.startswith(_ACTUATOR_PREFIXES) or prefix.startswith(_BEHAVIORAL_CONTROLLER_PREFIXES):
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
