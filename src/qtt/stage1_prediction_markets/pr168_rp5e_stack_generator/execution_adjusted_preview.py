"""Execution-adjusted stack preview facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def execution_preview_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "exec_prev.jsonl")
