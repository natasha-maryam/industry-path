from __future__ import annotations


class ProcessDynamicsService:
    """Stub extension point for dynamic process behavior inference."""

    def estimate_time_constant(self, process_unit: str | None) -> float:
        # TODO: infer from documents/simulation results.
        if not process_unit:
            return 1.0
        return 1.0


process_dynamics_service = ProcessDynamicsService()
