"""Use-and-dump retention policy facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def use_dump_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "use_dump.jsonl")
