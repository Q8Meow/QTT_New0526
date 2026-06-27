"""Quantum solver compatibility facade."""

from __future__ import annotations

from .models import GENERATED_DIR, read_jsonl


def quantum_solver_rows() -> list[dict[str, object]]:
    return read_jsonl(GENERATED_DIR / "q_solver.jsonl")
