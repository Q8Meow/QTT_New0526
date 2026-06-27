"""Cheap prescreen facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def prescreen_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "prescreen.jsonl")
