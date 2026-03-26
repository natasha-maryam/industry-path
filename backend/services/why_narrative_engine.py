from __future__ import annotations

from typing import Any, Mapping


class WhyNarrativeEngine:
    def build(
        self,
        *,
        target_tag: str,
        target_role: str,
        target_type: str | None,
        target_subtype: str | None,
        behavior_summary: str | None,
        ranked_upstream: list[Mapping[str, Any]],
        ranked_downstream: list[Mapping[str, Any]],
        runtime_state: Mapping[str, Any] | None,
        diagnostics_reason: str | None,
    ) -> dict[str, Any]:
        safe_tag = str(target_tag or "").strip() or "unknown-tag"
        safe_role = str(target_role or "unknown").strip() or "unknown"
        safe_type = str(target_type or "").strip()
        safe_subtype = str(target_subtype or "").strip()
        safe_summary = str(behavior_summary or "").strip()

        strongest_upstream = self._pick_best_chain(ranked_upstream)
        strongest_downstream = self._pick_best_chain(ranked_downstream)

        summary = self._build_summary(
            target_tag=safe_tag,
            target_role=safe_role,
            target_type=safe_type,
            target_subtype=safe_subtype,
            strongest_upstream=strongest_upstream,
            strongest_downstream=strongest_downstream,
        )
        behavior = self._build_behavior_text(
            target_tag=safe_tag,
            behavior_summary=safe_summary,
            strongest_upstream=strongest_upstream,
            strongest_downstream=strongest_downstream,
        )
        upstream_text = self._build_upstream_text(safe_tag, strongest_upstream)
        downstream_text = self._build_downstream_text(safe_tag, strongest_downstream)
        state_text = self._build_state_text(safe_tag, runtime_state, strongest_upstream, strongest_downstream)
        warnings = self._build_warnings(
            ranked_upstream=ranked_upstream,
            ranked_downstream=ranked_downstream,
            diagnostics_reason=diagnostics_reason,
        )

        return {
            "summary": summary,
            "behavior": behavior,
            "upstream": upstream_text,
            "downstream": downstream_text,
            "state": state_text,
            "warnings": warnings,
        }

    def _pick_best_chain(self, chains: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
        if not chains:
            return None

        def sort_key(item: Mapping[str, Any]) -> tuple[float, int, str]:
            score_raw = item.get("score")
            try:
                score = float(score_raw)
            except (TypeError, ValueError):
                score = 0.0
            tags = [str(tag).strip() for tag in (item.get("tags", []) or []) if str(tag).strip()]
            return (score, len(tags), "|".join(tags))

        return sorted(chains, key=sort_key, reverse=True)[0]

    def _normalized_tags(self, chain: Mapping[str, Any] | None) -> list[str]:
        if not chain:
            return []
        return [str(tag).strip() for tag in (chain.get("tags", []) or []) if str(tag).strip()]

    def _build_summary(
        self,
        *,
        target_tag: str,
        target_role: str,
        target_type: str,
        target_subtype: str,
        strongest_upstream: Mapping[str, Any] | None,
        strongest_downstream: Mapping[str, Any] | None,
    ) -> str:
        role_segment = f"{target_tag} is acting as {target_role}"
        if target_type:
            role_segment += f" ({target_type}"
            role_segment += f"/{target_subtype}" if target_subtype else ""
            role_segment += ")"
        role_segment += "."

        up_tags = self._normalized_tags(strongest_upstream)
        down_tags = self._normalized_tags(strongest_downstream)

        if up_tags:
            if up_tags[0] == target_tag:
                up_path = list(reversed(up_tags))
            else:
                up_path = up_tags
            upstream_segment = f" Strongest upstream context: {' -> '.join(up_path)}."
        else:
            upstream_segment = " No ranked upstream context is currently available."

        if down_tags:
            downstream_segment = f" Strongest downstream context: {' -> '.join(down_tags)}."
        else:
            downstream_segment = " No ranked downstream context is currently available."

        return f"{role_segment}{upstream_segment}{downstream_segment}".strip()

    def _build_behavior_text(
        self,
        *,
        target_tag: str,
        behavior_summary: str,
        strongest_upstream: Mapping[str, Any] | None,
        strongest_downstream: Mapping[str, Any] | None,
    ) -> str:
        segments: list[str] = []
        if behavior_summary:
            segments.append(behavior_summary)

        up_tags = self._normalized_tags(strongest_upstream)
        if up_tags:
            up_path = list(reversed(up_tags)) if up_tags and up_tags[0] == target_tag else up_tags
            segments.append(f"Primary upstream influence path is {' -> '.join(up_path)}")

        down_tags = self._normalized_tags(strongest_downstream)
        if down_tags:
            segments.append(f"Primary downstream impact path is {' -> '.join(down_tags)}")

        if not segments:
            return f"No deterministic behavior narrative is available yet for {target_tag}."

        return "; ".join(segments) + "."

    def _build_upstream_text(self, target_tag: str, strongest_upstream: Mapping[str, Any] | None) -> str:
        up_tags = self._normalized_tags(strongest_upstream)
        if not up_tags:
            return f"No upstream origin chain is available for {target_tag}."

        path = list(reversed(up_tags)) if up_tags and up_tags[0] == target_tag else up_tags
        origin = path[0] if path else target_tag
        return f"Upstream origin for {target_tag} traces from {origin} through {' -> '.join(path)}."

    def _build_downstream_text(self, target_tag: str, strongest_downstream: Mapping[str, Any] | None) -> str:
        down_tags = self._normalized_tags(strongest_downstream)
        if not down_tags:
            return f"No downstream impact chain is available for {target_tag}."

        impact = down_tags[-1] if down_tags else target_tag
        return f"Downstream impact from {target_tag} propagates along {' -> '.join(down_tags)} and reaches {impact}."

    def _build_state_text(
        self,
        target_tag: str,
        runtime_state: Mapping[str, Any] | None,
        strongest_upstream: Mapping[str, Any] | None,
        strongest_downstream: Mapping[str, Any] | None,
    ) -> str:
        runtime = dict(runtime_state or {})
        current_value = str(runtime.get("current_value") or "").strip()
        state = str(runtime.get("state") or "").strip()
        mode = str(runtime.get("mode") or "").strip()
        setpoint = str(runtime.get("setpoint") or "").strip()
        unit = str(runtime.get("unit") or "").strip()

        runtime_parts: list[str] = []
        if current_value:
            runtime_parts.append(f"value={current_value}{(' ' + unit) if unit else ''}")
        if state:
            runtime_parts.append(f"state={state}")
        if mode:
            runtime_parts.append(f"mode={mode}")
        if setpoint:
            runtime_parts.append(f"setpoint={setpoint}")

        if runtime_parts:
            return f"Runtime state for {target_tag}: {', '.join(runtime_parts)}."

        if self._normalized_tags(strongest_upstream) or self._normalized_tags(strongest_downstream):
            return f"Runtime state for {target_tag} is unavailable; narrative is derived from structural chain relationships."

        return f"Runtime state for {target_tag} is unavailable and no structural chain context is currently available."

    def _build_warnings(
        self,
        *,
        ranked_upstream: list[Mapping[str, Any]],
        ranked_downstream: list[Mapping[str, Any]],
        diagnostics_reason: str | None,
    ) -> list[str]:
        warnings: list[str] = []
        all_chains = list(ranked_upstream) + list(ranked_downstream)

        broken_upstream = sum(1 for chain in ranked_upstream if bool(chain.get("broken", False)))
        broken_downstream = sum(1 for chain in ranked_downstream if bool(chain.get("broken", False)))
        if broken_upstream:
            warnings.append(f"Detected {broken_upstream} broken upstream chain(s).")
        if broken_downstream:
            warnings.append(f"Detected {broken_downstream} broken downstream chain(s).")

        weak_link_count = 0
        low_confidence_count = 0
        for chain in all_chains:
            weak_links = chain.get("weak_links", []) or []
            weak_link_count += len(weak_links)
            for weak in weak_links:
                reasons = [str(item).strip() for item in (weak.get("reasons", []) or []) if str(item).strip()]
                if "low_confidence" in reasons:
                    low_confidence_count += 1

        if weak_link_count:
            warnings.append(f"Detected {weak_link_count} weak relationship link(s) across ranked chains.")
        if low_confidence_count:
            warnings.append(f"Detected {low_confidence_count} low-confidence relationship(s).")

        safe_reason = str(diagnostics_reason or "").strip()
        if safe_reason:
            warnings.append(f"Chain resolution diagnostic: {safe_reason}.")

        if not warnings:
            warnings.append("No chain integrity warnings detected.")

        return sorted(set(warnings))
