"""Stack template registry facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def template_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "templates.jsonl")
