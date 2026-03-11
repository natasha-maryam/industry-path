from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz, process

from services.normalize_tags import normalize_canonical_tag


@dataclass(frozen=True)
class ReconciledTag:
    query: str
    matched: str
    score: float


def reconcile_tag(query_tag: str, candidates: list[str], threshold: float = 82.0) -> ReconciledTag | None:
    if not query_tag or not candidates:
        return None
    normalized_query = normalize_canonical_tag(query_tag)
    normalized_candidates = {normalize_canonical_tag(item): item for item in candidates}
    result = process.extractOne(normalized_query, list(normalized_candidates.keys()), scorer=fuzz.token_sort_ratio)
    if result is None:
        return None
    match, score, _ = result
    if score < threshold:
        return None
    return ReconciledTag(query=query_tag, matched=normalized_candidates[match], score=float(score))


def reconcile_tags_bulk(query_tags: list[str], candidates: list[str], threshold: float = 82.0) -> dict[str, ReconciledTag]:
    output: dict[str, ReconciledTag] = {}
    for tag in query_tags:
        reconciled = reconcile_tag(tag, candidates, threshold=threshold)
        if reconciled is not None:
            output[tag] = reconciled
    return output
