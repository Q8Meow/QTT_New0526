"""Future handoff facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_json, read_jsonl


def downstream_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "downstream.jsonl")


def handoff_report(filename: str) -> dict[str, object]:
    return read_json(GENERATED_DIR / filename)
