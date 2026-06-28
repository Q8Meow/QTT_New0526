"""Value lineage facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def value_lineage_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "lineage.jsonl")
