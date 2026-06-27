"""QKU computability guard facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def qku_guard_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "qku_guard.jsonl")
