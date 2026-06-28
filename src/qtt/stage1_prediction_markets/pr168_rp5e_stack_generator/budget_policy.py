"""Stack generator budget policy facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def budget_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "budget.jsonl")
