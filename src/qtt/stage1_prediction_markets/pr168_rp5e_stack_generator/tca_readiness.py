"""TCA readiness decomposition facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def tca_readiness_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "tca_ready.jsonl")
