"""Marginal utility feature facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def marginal_utility_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "marg_util.jsonl")
