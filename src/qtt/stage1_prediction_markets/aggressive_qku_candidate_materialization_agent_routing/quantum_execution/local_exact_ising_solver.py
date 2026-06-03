"""Tiny deterministic exact Ising enumerator."""

from __future__ import annotations

from itertools import product
from typing import Any

from .ising_model import validate_ising_terms
from .objective_value_calculator import ising_objective_value


def solve_ising_exact(
    h: list[float] | tuple[float, ...],
    j: list[tuple[int, int, float]] | tuple[tuple[int, int, float], ...],
    *,
    max_variables: int = 12,
) -> dict[str, Any]:
    fields, couplers = validate_ising_terms(h, j)
    if len(fields) > max_variables:
        raise ValueError("Ising exact smoke variable count exceeds cap")
    best_spins: tuple[int, ...] | None = None
    best_energy: float | None = None
    evaluated = 0
    for spins in product((-1, 1), repeat=len(fields)):
        evaluated += 1
        energy = ising_objective_value(spins, fields, couplers)
        if best_energy is None or energy < best_energy:
            best_energy = energy
            best_spins = spins
    return {
        "best_assignment": list(best_spins or ()),
        "best_objective_value": best_energy,
        "evaluated_assignment_count": evaluated,
        "variable_count": len(fields),
        "smoke_execution_status": "QUANTUM_LOCAL_SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
    }
