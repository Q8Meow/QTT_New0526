"""Search budget trace facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def search_trace_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "search_trace.jsonl")
