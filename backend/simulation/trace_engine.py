from __future__ import annotations

import time
from typing import Any, Callable


class SimulationTraceEngine:
    def __init__(self) -> None:
        self.timeline: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.timeline = []

    def record(self, tag: str, value: Any, t: int) -> None:
        self.timeline.append(
            {
                "tag": tag,
                "value": value,
                "time": t,
            }
        )

    def run_step(
        self,
        runtime_reader: Callable[[], dict[str, Any]],
        *,
        step_ms: int = 100,
        duration_ms: int = 10_000,
        reset: bool = True,
        start_at_ms: int = 0,
    ) -> list[dict[str, Any]]:
        if reset:
            self.reset()
        t = max(start_at_ms, 0)
        end_t = t + max(duration_ms, 0)
        while t <= end_t:
            state = runtime_reader() or {}
            for tag, val in state.items():
                self.record(tag, val, t)
            time.sleep(max(step_ms, 10) / 1000)
            t += max(step_ms, 10)
        return self.timeline

    def export(self) -> list[dict[str, Any]]:
        return list(self.timeline)
