from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class NormalizedTagRecord:
    raw_tag: str
    canonical_tag: str


def normalize_canonical_tag(raw_tag: str) -> str:
    cleaned = (raw_tag or "").strip().upper()
    cleaned = cleaned.replace(" ", "").replace("/", "-").replace(".", "")
    cleaned = re.sub(r"_+", "", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)

    match = re.match(r"^([A-Z]{1,6})-?(\d{1,5})([A-Z]{0,3})$", cleaned)
    if not match:
        return cleaned.strip("-")
    prefix, number, suffix = match.groups()
    canonical = f"{prefix}-{int(number)}"
    if suffix:
        canonical = f"{canonical}{suffix}"
    return canonical


def normalize_tag_table(raw_tags: list[str]) -> list[NormalizedTagRecord]:
    frame = pd.DataFrame({"raw_tag": raw_tags})
    frame["canonical_tag"] = frame["raw_tag"].astype(str).map(normalize_canonical_tag)
    frame = frame.drop_duplicates(subset=["canonical_tag"], keep="first")
    return [NormalizedTagRecord(raw_tag=row.raw_tag, canonical_tag=row.canonical_tag) for row in frame.itertuples(index=False)]
