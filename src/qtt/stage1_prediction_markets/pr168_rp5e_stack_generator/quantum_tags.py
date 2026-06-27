"""Quantum tag facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def quantum_tag_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "q_tags.jsonl")
