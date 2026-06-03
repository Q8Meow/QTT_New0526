"""Quantum formulation acquisition facade."""

from __future__ import annotations

from typing import Any

from .candidate_catalog import quantum_candidates


def quantum_formula_records(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    return quantum_candidates(sources, qku_pool)
