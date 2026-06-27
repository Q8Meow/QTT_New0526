"""Overfit/FDR control facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def fdr_control_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "fdr_ctrl.jsonl")
