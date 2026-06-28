"""Champion/challenger preview facade with no selection authority."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def champion_challenger_preview_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "champ_prev.jsonl")
