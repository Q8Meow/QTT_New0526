"""Stack generator facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def preview_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "tmp_previews.jsonl")


def topk_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "topk.jsonl")
