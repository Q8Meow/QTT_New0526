"""Edge/alpha feature facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def edge_feature_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "edge_feats.jsonl")


def alpha_hint_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "alpha_hints.jsonl")
