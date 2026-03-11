from __future__ import annotations

import json
import logging

from models.logic import SimulationScenarioResult, SimulationValidationResult
from services.project_service import project_service


class VirtualCommissioningService:
    """Simulation validation hook set for commissioning scenarios."""

    SCENARIOS = [
        "startup_sequence",
        "shutdown_sequence",
        "high_level_alarm",
        "low_level_alarm",
        "actuator_failure",
        "stuck_valve",
        "pump_failure",
        "sensor_out_of_range",
    ]

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def run(self, project_id: str) -> SimulationValidationResult:
        scenarios = [
            SimulationScenarioResult(
                scenario=item,
                status="todo",
                details="TODO: Connect scenario to digital twin/open-loop simulator adapter.",
            )
            for item in self.SCENARIOS
        ]

        result = SimulationValidationResult(project_id=project_id, overall_status="todo", scenarios=scenarios)
        paths = project_service.workspace_paths(project_id)
        out_file = paths.simulation_models / "virtual_commissioning.json"
        out_file.write_text(json.dumps(result.model_dump(), indent=2))
        self.logger.info("Virtual commissioning scenarios prepared: project=%s scenarios=%s", project_id, len(scenarios))
        return result


virtual_commissioning_service = VirtualCommissioningService()
