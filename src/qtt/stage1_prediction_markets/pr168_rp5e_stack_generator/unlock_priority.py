"""Executable-now unlock priority facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def unlock_priority_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "unlock_pri.jsonl")
