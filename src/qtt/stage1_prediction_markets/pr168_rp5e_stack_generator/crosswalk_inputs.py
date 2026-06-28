"""Optional route/crosswalk consumption facade for RP5E."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def route_crosswalk_consumption() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "xwalk_cons.jsonl")
