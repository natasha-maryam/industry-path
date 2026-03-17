from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from runtime_engine.runtime_manager import runtime_manager
from runtime_engine.runtime_signal_state import runtime_signal_state
from runtime_engine.runtime_telemetry import runtime_telemetry


class RuntimeEvaluator:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._lock = RLock()
        self._last_cycle: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    def _evaluate_command_status_links(self, values: dict[str, Any], evaluated_blocks: list[str]) -> None:
        changed = False
        for tag, value in list(values.items()):
            if not tag.endswith("_CMD"):
                continue
            status_tag = f"{tag[:-4]}_STATUS"
            if status_tag in values:
                next_value = self._as_bool(value)
                if values.get(status_tag) != next_value:
                    values[status_tag] = next_value
                    changed = True
            running_tag = f"{tag[:-4]}_RUNNING"
            if running_tag in values:
                next_running = self._as_bool(value)
                if values.get(running_tag) != next_running:
                    values[running_tag] = next_running
                    changed = True
        if changed:
            evaluated_blocks.append("command_status_links")

    def _evaluate_alarm_thresholds(self, values: dict[str, Any], evaluated_blocks: list[str]) -> dict[str, bool]:
        alarms: dict[str, bool] = {}
        changed = False

        def set_alarm(name: str, active: bool) -> None:
            nonlocal changed
            alarms[name] = active
            if values.get(name) != active:
                values[name] = active
                changed = True

        for tag, value in list(values.items()):
            if not self._is_numeric(value):
                continue
            number = float(value)
            upper_tag = tag.upper()

            if upper_tag.startswith(("LIT", "LT")) or upper_tag.endswith("_LEVEL"):
                set_alarm(f"{tag}_HI_ALARM", number >= 80.0)
                set_alarm(f"{tag}_HH_ALARM", number >= 95.0)
                set_alarm(f"{tag}_LO_ALARM", number <= 20.0)
                set_alarm(f"{tag}_LL_ALARM", number <= 5.0)
            elif upper_tag.startswith(("FIT", "FT")) or "FLOW" in upper_tag:
                set_alarm(f"{tag}_LOW_FLOW_ALARM", number <= 10.0)
                set_alarm(f"{tag}_HIGH_FLOW_ALARM", number >= 90.0)
            elif upper_tag.startswith(("PIT", "PT")) or "PRESS" in upper_tag:
                set_alarm(f"{tag}_HIGH_PRESSURE_ALARM", number >= 85.0)
                set_alarm(f"{tag}_LOW_PRESSURE_ALARM", number <= 15.0)

        if alarms:
            active_any = any(alarms.values())
            if values.get("PLANT_FAULT_ACTIVE") != active_any:
                values["PLANT_FAULT_ACTIVE"] = active_any
                changed = True

        if changed or alarms:
            evaluated_blocks.append("alarm_thresholds")
        return alarms

    def _evaluate_health_checks(
        self,
        values: dict[str, Any],
        forced_tags: list[str],
        alarms: dict[str, bool],
        evaluated_blocks: list[str],
    ) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        active_alarm_count = sum(1 for active in alarms.values() if active)

        runtime_status = runtime_manager.status().get("runtime", {}).get("status", "stopped")
        checks.append(
            {
                "name": "runtime_process",
                "status": "healthy" if runtime_status == "running" else "warning",
                "message": f"Runtime process state is {runtime_status}.",
            }
        )

        checks.append(
            {
                "name": "forced_inputs",
                "status": "warning" if forced_tags else "healthy",
                "message": f"{len(forced_tags)} input tag(s) currently forced.",
            }
        )

        checks.append(
            {
                "name": "alarm_flood",
                "status": "unhealthy" if active_alarm_count >= 4 else "healthy",
                "message": f"{active_alarm_count} active alarm(s).",
            }
        )

        numeric_values = [float(item) for item in values.values() if self._is_numeric(item)]
        has_nan = any(math.isnan(item) for item in numeric_values)
        checks.append(
            {
                "name": "signal_sanity",
                "status": "unhealthy" if has_nan else "healthy",
                "message": "Numeric signal sanity check passed." if not has_nan else "Detected NaN numeric signal values.",
            }
        )

        evaluated_blocks.append("health_checks")
        return checks

    @staticmethod
    def _dict_changes(previous: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        all_keys = sorted(set(previous.keys()) | set(current.keys()))
        for key in all_keys:
            old = previous.get(key)
            new = current.get(key)
            if old != new:
                changes.append({"tag": key, "previous": old, "current": new})
        return changes

    @staticmethod
    def _health_changes(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prev_by_name = {item.get("name"): item for item in previous}
        curr_by_name = {item.get("name"): item for item in current}
        names = sorted(set(prev_by_name.keys()) | set(curr_by_name.keys()))
        changes: list[dict[str, Any]] = []
        for name in names:
            old = prev_by_name.get(name)
            new = curr_by_name.get(name)
            if old != new:
                changes.append({"name": name, "previous": old, "current": new})
        return changes

    def run_cycle(
        self,
        project_id: str,
        *,
        reason: str,
        forced_tag: str | None = None,
        forced_value: Any | None = None,
        baseline_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = runtime_signal_state.get_project_snapshot(project_id)
        current_snapshot_values = dict(snapshot.get("current_values", {}))
        before_values = dict(baseline_values) if baseline_values is not None else dict(current_snapshot_values)
        forced_inputs = snapshot.get("forced_inputs", [])
        forced_tags = [str(item.get("tag")) for item in forced_inputs if item.get("tag")]
        evaluated_blocks: list[str] = []

        working_values = dict(current_snapshot_values)
        self._evaluate_command_status_links(working_values, evaluated_blocks)
        alarms = self._evaluate_alarm_thresholds(working_values, evaluated_blocks)
        health_checks = self._evaluate_health_checks(working_values, forced_tags, alarms, evaluated_blocks)

        after_values = runtime_signal_state.apply_evaluated_values(project_id, working_values)

        previous_cycle = self._last_cycle.get(project_id, {})
        previous_alarms = previous_cycle.get("alarms", {}) if isinstance(previous_cycle.get("alarms"), dict) else {}
        previous_health = previous_cycle.get("health_checks", []) if isinstance(previous_cycle.get("health_checks"), list) else []

        changed_signals = self._dict_changes(before_values, after_values)
        if forced_tag and forced_tag in after_values:
            previous_forced_value = before_values.get(forced_tag)
            current_forced_value = after_values.get(forced_tag)
            has_forced_entry = any(item.get("tag") == forced_tag for item in changed_signals)
            if previous_forced_value != current_forced_value and not has_forced_entry:
                changed_signals.insert(
                    0,
                    {
                        "tag": forced_tag,
                        "previous": previous_forced_value,
                        "current": current_forced_value,
                    },
                )
        changed_alarms = self._dict_changes(previous_alarms, alarms)
        changed_health_checks = self._health_changes(previous_health, health_checks)

        with self._lock:
            self._last_cycle[project_id] = {
                "project_id": project_id,
                "reason": reason,
                "evaluated_at": self._now_iso(),
                "forced_tag": forced_tag,
                "forced_value": forced_value,
                "evaluated_blocks": evaluated_blocks,
                "alarms": alarms,
                "health_checks": health_checks,
                "changed_signals": changed_signals,
                "changed_alarms": changed_alarms,
                "changed_health_checks": changed_health_checks,
                "signal_state_updated": len(changed_signals) > 0,
            }

        runtime_telemetry.update_tag("DIAGNOSTICS_HEALTH_CHECKS", health_checks)
        runtime_telemetry.update_tag("DIAGNOSTICS_ACTIVE_ALARMS", sorted([name for name, active in alarms.items() if active]))
        runtime_telemetry.update_tag("DIAGNOSTICS_LAST_EVALUATED_AT", self._now_iso())
        runtime_telemetry.update_tag("DIAGNOSTICS_EVALUATED_BLOCKS", evaluated_blocks)
        runtime_telemetry.update_tag("LAST_CHANGED_SIGNAL_TAGS", [item.get("tag") for item in changed_signals])
        runtime_telemetry.update_tag(
            "LAST_CHANGED_SIGNAL_VALUES",
            {item.get("tag"): item.get("current") for item in changed_signals if item.get("tag")},
        )

        self.logger.info(
            "runtime_eval force_tag=%s force_value=%s signal_state_updated=%s evaluated_blocks=%s changed_signals=%s changed_alarms=%s changed_health=%s",
            forced_tag,
            forced_value,
            len(changed_signals) > 0,
            evaluated_blocks,
            len(changed_signals),
            len(changed_alarms),
            len(changed_health_checks),
        )

        return self.get_last_cycle(project_id)

    def get_last_cycle(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            payload = self._last_cycle.get(project_id)
            if payload:
                return dict(payload)

        return {
            "project_id": project_id,
            "reason": "none",
            "evaluated_at": self._now_iso(),
            "forced_tag": None,
            "forced_value": None,
            "evaluated_blocks": [],
            "alarms": {},
            "health_checks": [],
            "changed_signals": [],
            "changed_alarms": [],
            "changed_health_checks": [],
            "signal_state_updated": False,
        }


runtime_evaluator = RuntimeEvaluator()
