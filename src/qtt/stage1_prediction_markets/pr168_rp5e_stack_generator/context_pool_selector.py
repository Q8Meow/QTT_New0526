"""Context formula pool selector facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def context_pool_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "ctx_pools.jsonl")
