"""No-orphan proof facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def no_orphan_artifact_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "orph_art.jsonl")


def no_orphan_qku_formula_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "orph_qku.jsonl")
