"""Classical fallback tag facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def classical_fallback_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "classic.jsonl")
