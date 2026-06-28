"""File route registry facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def file_route_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "file_route.jsonl")
