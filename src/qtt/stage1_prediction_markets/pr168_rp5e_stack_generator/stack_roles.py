"""Stack role ontology facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def role_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "roles.jsonl")
