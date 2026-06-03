"""Quantum problem formulation registry facade."""

from __future__ import annotations

from typing import Any


def quantum_problem_formulation_records(quantum: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **record,
            "quantum_problem_formulation_candidate_flag": True,
            "classical_comparator_required_flag": True,
        }
        for record in quantum
    ]
