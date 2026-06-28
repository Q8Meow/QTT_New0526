"""Regime-conditioned memory hint facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def regime_memory_hint_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "regime_mem.jsonl")
