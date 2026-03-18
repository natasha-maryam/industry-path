from __future__ import annotations

from typing import Any


def analyze_trace(trace: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    tag_names = {str(item.get("tag", "")) for item in trace if item.get("tag")}

    for tag in sorted(tag_names):
        values = [item.get("value") for item in trace if str(item.get("tag", "")) == tag]
        numeric_values = [float(value) for value in values if isinstance(value, (int, float))]

        if numeric_values and (max(numeric_values) - min(numeric_values) > 50):
            issues.append({"tag": tag, "issue": "unstable_signal"})

        if len(values) > 10 and values[-1] is not None and values[-10:].count(values[-1]) >= 10:
            issues.append({"tag": tag, "issue": "stuck_signal"})

    return issues
