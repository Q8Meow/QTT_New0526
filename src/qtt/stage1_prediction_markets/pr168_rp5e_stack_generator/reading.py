"""Reading and input-consumption facade for RP5E."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def reading_receipts() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "read_rec.jsonl")


def input_consumption_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "in_cons.jsonl")
