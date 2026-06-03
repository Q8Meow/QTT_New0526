"""Tiny deterministic exact QUBO enumerator."""

from __future__ import annotations

from itertools import product
from typing import Any

from .objective_value_calculator import qubo_objective_value
from .qubo_model import validate_qubo_matrix


def solve_qubo_exact(q_matrix: list[list[float]] | tuple[tuple[float, ...], ...], *, max_variables: int = 12) -> dict[str, Any]:
    matrix = validate_qubo_matrix(q_matrix)
    if len(matrix) > max_variables:
        raise ValueError("QUBO exact smoke variable count exceeds cap")
    best_bits: tuple[int, ...] | None = None
    best_energy: float | None = None
    evaluated = 0
    for bits in product((0, 1), repeat=len(matrix)):
        evaluated += 1
        energy = qubo_objective_value(bits, matrix)
        if best_energy is None or energy < best_energy:
            best_energy = energy
            best_bits = bits
    return {
        "best_assignment": list(best_bits or ()),
        "best_objective_value": best_energy,
        "evaluated_assignment_count": evaluated,
        "variable_count": len(matrix),
        "smoke_execution_status": "QUANTUM_LOCAL_SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
    }
