from datetime import datetime, timezone
import json
from threading import RLock

from runtime_engine.runtime_signal_state import runtime_signal_state
from runtime_engine.runtime_telemetry import runtime_telemetry
from simulation.analysis import analyze_trace
from simulation.trace_engine import SimulationTraceEngine
from services.graph_service import graph_service
from services.project_service import project_service


class SimulationService:
    def __init__(self) -> None:
        self.trace_engine = SimulationTraceEngine()
        self._lock = RLock()
        self._trace_by_project: dict[str, list[dict[str, object]]] = {}

    def _latest_file(self, project_id: str):
        paths = project_service.workspace_paths(project_id)
        return paths.simulation_models / "latest_run.json"

    def _trace_file(self, project_id: str):
        paths = project_service.workspace_paths(project_id)
        return paths.simulation_models / "latest_trace.json"

    @staticmethod
    def _to_numeric_or_text(value: object) -> object:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "false"}:
                return normalized == "true"
            try:
                numeric = float(value.strip())
            except ValueError:
                return 0
            if numeric.is_integer():
                return int(numeric)
            return numeric
        if value is None:
            return 0
        return 0

    @staticmethod
    def _normalize_trace_row(row: dict[str, object]) -> dict[str, object] | None:
        tag = str(row.get("tag") or "").strip()
        if not tag:
            return None
        time_value = row.get("time")
        try:
            time_ms = int(time_value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            time_ms = 0
        value = SimulationService._to_numeric_or_text(row.get("value"))
        return {
            "tag": tag,
            "value": value,
            "time": max(time_ms, 0),
        }

    def _load_trace_from_file(self, project_id: str) -> list[dict[str, object]]:
        trace_file = self._trace_file(project_id)
        if not trace_file.exists():
            return []
        try:
            payload = json.loads(trace_file.read_text())
        except Exception:
            return []
        if not isinstance(payload, list):
            return []
        normalized: list[dict[str, object]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            row = self._normalize_trace_row(item)
            if row:
                normalized.append(row)
        return normalized

    def _save_trace(self, project_id: str, trace: list[dict[str, object]]) -> None:
        trace_file = self._trace_file(project_id)
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        trace_file.write_text(json.dumps(trace, indent=2))

    def _get_cached_trace(self, project_id: str) -> list[dict[str, object]]:
        cached = self._trace_by_project.get(project_id)
        if cached is not None:
            return list(cached)
        loaded = self._load_trace_from_file(project_id)
        self._trace_by_project[project_id] = list(loaded)
        return list(loaded)

    def _runtime_tags_with_fallback(self, project_id: str) -> dict[str, object]:
        snapshot = runtime_signal_state.get_project_snapshot(project_id)
        snapshot_values = snapshot.get("current_values", {}) if isinstance(snapshot, dict) else {}
        if isinstance(snapshot_values, dict) and snapshot_values:
            return {tag: self._to_numeric_or_text(value) for tag, value in snapshot_values.items() if str(tag).strip()}

        tags = runtime_telemetry.get_all_tags()
        if tags:
            return {tag: self._to_numeric_or_text(value) for tag, value in tags.items()}

        graph = graph_service.get_graph(project_id)
        fallback: dict[str, object] = {}
        for node in graph.nodes[:20]:
            fallback[node.id] = 0
        if not fallback:
            fallback["SIM_HEARTBEAT"] = 1
        return fallback

    def capture_trace(
        self,
        project_id: str,
        *,
        reset: bool = False,
        step_ms: int = 100,
        duration_ms: int = 1500,
    ) -> list[dict[str, object]]:
        project_service.ensure_project(project_id)
        with self._lock:
            existing = [] if reset else self._get_cached_trace(project_id)
            next_start = 0 if not existing else int(existing[-1].get("time") or 0) + max(step_ms, 10)

            self.trace_engine.timeline = list(existing)
            captured = self.trace_engine.run_step(
                lambda: self._runtime_tags_with_fallback(project_id),
                step_ms=step_ms,
                duration_ms=duration_ms,
                reset=reset,
                start_at_ms=next_start,
            )

            normalized: list[dict[str, object]] = []
            for item in captured:
                if not isinstance(item, dict):
                    continue
                row = self._normalize_trace_row(item)
                if row:
                    normalized.append(row)

            self._trace_by_project[project_id] = list(normalized)
            self._save_trace(project_id, normalized)
            return list(normalized)

    def reset_trace(self, project_id: str) -> list[dict[str, object]]:
        project_service.ensure_project(project_id)
        with self._lock:
            self.trace_engine.reset()
            self._trace_by_project[project_id] = []
            self._save_trace(project_id, [])
            return []

    def run(self, project_id: str) -> dict[str, object]:
        project_service.ensure_project(project_id)

        trace = self.capture_trace(project_id, reset=True, step_ms=100, duration_ms=3000)
        issues = analyze_trace(trace)

        metrics = {
            "samples": len(trace),
            "tags": len({str(item.get("tag", "")) for item in trace if item.get("tag")}),
            "issues": issues,
            "scenarios": [
                {
                    "scenario_id": "trace_stability",
                    "scenario_name": "Signal Stability Check",
                    "status": "warning" if issues else "success",
                    "cycle_time_ms": 100,
                    "duration_s": 3,
                    "alarms_triggered": len(issues),
                    "message": "Trace analysis completed",
                }
            ],
        }

        payload = {
            "project_id": project_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "metrics": metrics,
        }
        self._latest_file(project_id).write_text(json.dumps(payload, indent=2))
        return payload

    def latest(self, project_id: str) -> dict[str, object]:
        project_service.ensure_project(project_id)
        latest_file = self._latest_file(project_id)
        if not latest_file.exists():
            return {"project_id": project_id, "status": "not-run", "metrics": {}}
        return json.loads(latest_file.read_text())

    def trace(self, project_id: str) -> list[dict[str, object]]:
        project_service.ensure_project(project_id)
        with self._lock:
            return self._get_cached_trace(project_id)

    def trace_analysis(self, project_id: str) -> list[dict[str, str]]:
        return analyze_trace(self.trace(project_id))


simulation_service = SimulationService()
