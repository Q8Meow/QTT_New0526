"""Candidate family exposure facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def candidate_family_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "cand_fam.jsonl")
