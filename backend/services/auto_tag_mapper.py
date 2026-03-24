from __future__ import annotations

from typing import Any

from services.uns_core import uns_core

try:
    from rapidfuzz import process as rapidfuzz_process  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    rapidfuzz_process = None


class AutoTagMapper:
    def __init__(self) -> None:
        self._default_threshold = 70.0

    @staticmethod
    def _tokenize(value: str) -> str:
        return "".join(ch for ch in value.upper() if ch.isalnum())

    def _best_match_fallback(self, candidate: str, choices: list[str]) -> tuple[str | None, float]:
        candidate_token = self._tokenize(candidate)
        if not candidate_token or not choices:
            return None, 0.0

        best: tuple[str | None, float] = (None, 0.0)
        for choice in choices:
            choice_token = self._tokenize(choice)
            if not choice_token:
                continue
            overlap = len(set(candidate_token) & set(choice_token))
            score = 100.0 * overlap / max(len(set(candidate_token)), 1)
            if score > best[1]:
                best = (choice, score)
        return best

    def auto_map(self, external_tags: list[str], threshold: float | None = None) -> dict[str, Any]:
        rows = uns_core.get_rows()
        uns_tags = [str(row.get("tag") or "").strip() for row in rows if str(row.get("tag") or "").strip()]
        min_score = self._default_threshold if threshold is None else float(threshold)

        mappings: list[dict[str, Any]] = []
        unmatched: list[str] = []

        for external in external_tags:
            external_tag = str(external or "").strip()
            if not external_tag:
                continue

            match_tag: str | None = None
            score: float = 0.0

            if rapidfuzz_process is not None and uns_tags:
                candidate = rapidfuzz_process.extractOne(external_tag, uns_tags)
                if candidate:
                    match_tag = str(candidate[0])
                    score = float(candidate[1])
            else:
                match_tag, score = self._best_match_fallback(external_tag, uns_tags)

            if not match_tag or score < min_score:
                unmatched.append(external_tag)
                continue

            mapped = uns_core.map_tag(
                match_tag,
                {
                    "external_tag": external_tag,
                    "score": round(score, 3),
                    "source": "auto_tag_mapper",
                },
            )
            mappings.append(
                {
                    "external_tag": external_tag,
                    "mapped_tag": match_tag,
                    "score": round(score, 3),
                    "mapping": mapped,
                }
            )

        return {
            "mapped": mappings,
            "unmatched": unmatched,
            "threshold": min_score,
            "count": len(mappings),
        }


auto_tag_mapper = AutoTagMapper()
