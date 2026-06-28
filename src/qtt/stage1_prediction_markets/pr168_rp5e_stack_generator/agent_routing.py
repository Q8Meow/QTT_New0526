"""Agent routing facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def agent_route_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "agent_route.jsonl")
