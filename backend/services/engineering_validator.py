from __future__ import annotations

import logging

from models.logic import EngineeringValidationReport, ValidationIssue
from models.pipeline import EngineeringEntity
from services.graph_service import graph_service
from services.normalize_tags import normalize_canonical_tag
from services.reconcile_tags import reconcile_tag


class EngineeringValidator:
    """Validate engineering model consistency before logic generation."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def validate(self, project_id: str, entities: list[EngineeringEntity]) -> EngineeringValidationReport:
        by_id: dict[str, EngineeringEntity] = {}
        grouped_by_tag: dict[str, list[EngineeringEntity]] = {}
        grouped_by_canonical_tag: dict[str, list[EngineeringEntity]] = {}

        for entity in entities:
            tag = entity.id.upper()
            grouped_by_tag.setdefault(tag, []).append(entity)
            canonical = normalize_canonical_tag(tag)
            grouped_by_canonical_tag.setdefault(canonical, []).append(entity)
            by_id[tag] = entity

        sensors = {
            item.id
            for item in entities
            if item.canonical_type
            in {
                "flow_transmitter",
                "level_transmitter",
                "level_switch",
                "pressure_transmitter",
                "differential_pressure_transmitter",
                "analyzer",
            }
        }
        actuators = {
            item.id
            for item in entities
            if item.canonical_type in {"pump", "control_valve", "valve", "blower", "chemical_system_device"}
        }

        graph = graph_service.get_graph(project_id)
        edge_pairs = {(edge.source.upper(), edge.target.upper(), edge.edge_type.upper()) for edge in graph.edges}
        node_ids = {node.id.upper() for node in graph.nodes}

        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        for tag, group in sorted(grouped_by_tag.items()):
            if len(group) <= 1:
                continue

            canonical_types = sorted({item.canonical_type for item in group})
            process_units = sorted({item.process_unit for item in group if item.process_unit})

            # Process-unit duplicates are often aliasing artifacts from topology assignment.
            # Keep them visible but non-fatal so downstream completion can continue.
            if canonical_types == ["process_unit"]:
                warnings.append(
                    ValidationIssue(
                        code="duplicate_tag_conflict",
                        severity="warning",
                        message=(
                            f"Conflicting duplicate process-unit tag detected (non-fatal): {tag} "
                            f"types={canonical_types} units={process_units or ['<none>']}"
                        ),
                        related_tags=[tag],
                    )
                )
                continue

            # Hard fail only when the same tag maps to conflicting non-process engineering meanings.
            if len(canonical_types) > 1 or len(process_units) > 1:
                errors.append(
                    ValidationIssue(
                        code="duplicate_tag_conflict",
                        severity="error",
                        message=(
                            f"Conflicting duplicate tag detected: {tag} "
                            f"types={canonical_types} units={process_units or ['<none>']}"
                        ),
                        related_tags=[tag],
                    )
                )
                continue

            warnings.append(
                ValidationIssue(
                    code="duplicate_tag",
                    severity="warning",
                    message=f"Duplicate engineering tag detected (merged as non-conflicting): {tag}",
                    related_tags=[tag],
                )
            )

        # Canonicalized duplicate check (LT101 vs LT-101, etc.).
        for canonical_tag, group in sorted(grouped_by_canonical_tag.items()):
            unique_ids = sorted({item.id.upper() for item in group})
            if len(unique_ids) > 1:
                warnings.append(
                    ValidationIssue(
                        code="canonical_tag_alias_detected",
                        severity="warning",
                        message=f"Canonical tag alias set detected for {canonical_tag}: {', '.join(unique_ids)}",
                        related_tags=unique_ids,
                    )
                )

        # Fuzzy near-duplicate warnings for messy OCR docs.
        all_tags = sorted(grouped_by_tag.keys())
        for tag in all_tags:
            candidates = [item for item in all_tags if item != tag]
            matched = reconcile_tag(tag, candidates, threshold=90.0)
            if matched and normalize_canonical_tag(tag) != normalize_canonical_tag(matched.matched):
                warnings.append(
                    ValidationIssue(
                        code="fuzzy_tag_collision",
                        severity="warning",
                        message=f"Potential fuzzy tag collision: {tag} ~ {matched.matched} ({matched.score:.1f})",
                        related_tags=[tag, matched.matched],
                    )
                )

        if not sensors:
            errors.append(
                ValidationIssue(
                    code="missing_sensors",
                    severity="error",
                    message="No sensor/instrument entities were detected in the engineering model.",
                )
            )

        if not actuators:
            errors.append(
                ValidationIssue(
                    code="missing_actuators",
                    severity="error",
                    message="No actuator entities were detected in the engineering model.",
                )
            )

        for actuator in sorted(actuators):
            has_signal = any(
                (src == actuator and edge_type in {"SIGNAL_TO", "CONTROLS"})
                or (dst == actuator and edge_type in {"SIGNAL_TO", "CONTROLS"})
                for src, dst, edge_type in edge_pairs
            )
            if not has_signal:
                warnings.append(
                    ValidationIssue(
                        code="missing_actuator_link",
                        severity="warning",
                        message=f"Actuator has no explicit control signal relationship: {actuator}",
                        related_tags=[actuator],
                    )
                )

        for sensor in sorted(sensors):
            has_signal_definition = any(
                (src == sensor and edge_type in {"MEASURES", "MONITORS", "SIGNAL_TO"})
                or (dst == sensor and edge_type in {"MEASURES", "MONITORS", "SIGNAL_TO"})
                for src, dst, edge_type in edge_pairs
            )
            if not has_signal_definition:
                warnings.append(
                    ValidationIssue(
                        code="missing_signal_definition",
                        severity="warning",
                        message=f"Sensor lacks explicit signal definition edge: {sensor}",
                        related_tags=[sensor],
                    )
                )

        # Production floor check: must have at least one sensor->actuator signal path candidate.
        loopable_pairs = 0
        for src, dst, edge_type in edge_pairs:
            if src in {item.upper() for item in sensors} and dst in {item.upper() for item in actuators} and edge_type in {"SIGNAL_TO", "CONTROLS", "MONITORS", "MEASURES"}:
                loopable_pairs += 1
        if loopable_pairs == 0:
            errors.append(
                ValidationIssue(
                    code="no_loopable_sensor_actuator_pairs",
                    severity="error",
                    message="No sensor-to-actuator signal paths were detected for control loop discovery.",
                )
            )

        for source, target, edge_type in sorted(edge_pairs):
            if source not in node_ids or target not in node_ids:
                errors.append(
                    ValidationIssue(
                        code="broken_signal_path",
                        severity="error",
                        message=f"Graph edge references missing node: {source} -[{edge_type}]-> {target}",
                        related_tags=[source, target],
                    )
                )

        status = "failed" if errors else "passed"
        self.logger.info(
            "Engineering validation completed: project=%s status=%s errors=%s warnings=%s",
            project_id,
            status,
            len(errors),
            len(warnings),
        )
        return EngineeringValidationReport(project_id=project_id, status=status, errors=errors, warnings=warnings)


engineering_validator = EngineeringValidator()
