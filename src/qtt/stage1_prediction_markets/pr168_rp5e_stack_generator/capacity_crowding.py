"""Capacity and crowding facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def capacity_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "capacity.jsonl")
