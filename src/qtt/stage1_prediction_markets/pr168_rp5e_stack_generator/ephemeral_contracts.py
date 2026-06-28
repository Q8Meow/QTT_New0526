"""Ephemeral stack run contract facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def ephemeral_contract_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "eph_contracts.jsonl")
