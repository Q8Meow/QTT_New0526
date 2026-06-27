"""Stack diversity ledger facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def diversity_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "diverse.jsonl")
