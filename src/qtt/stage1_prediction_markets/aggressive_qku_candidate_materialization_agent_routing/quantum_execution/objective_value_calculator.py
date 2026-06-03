"""Local deterministic objective value calculations."""

from __future__ import annotations

from .ising_model import validate_ising_terms
from .qubo_model import validate_qubo_matrix


def qubo_objective_value(
    bits: list[int] | tuple[int, ...],
    q_matrix: list[list[float]] | tuple[tuple[float, ...], ...],
    constant_offset: float = 0.0,
) -> float:
    matrix = validate_qubo_matrix(q_matrix)
    x = tuple(int(value) for value in bits)
    if len(x) != len(matrix):
        raise ValueError("QUBO bit vector length must match Q dimension")
    if any(value not in (0, 1) for value in x):
        raise ValueError("QUBO vector must be binary")
    total = float(constant_offset)
    total += sum(x[i] * matrix[i][j] * x[j] for i in range(len(x)) for j in range(len(x)))
    return total


def ising_objective_value(
    spins: list[int] | tuple[int, ...],
    h: list[float] | tuple[float, ...],
    j: list[tuple[int, int, float]] | tuple[tuple[int, int, float], ...],
    constant_offset: float = 0.0,
) -> float:
    fields, couplers = validate_ising_terms(h, j)
    s = tuple(int(value) for value in spins)
    if len(s) != len(fields):
        raise ValueError("Ising spin vector length must match h dimension")
    if any(value not in (-1, 1) for value in s):
        raise ValueError("Ising vector must contain -1 or 1 spins")
    total = float(constant_offset)
    total += sum(field * spin for field, spin in zip(fields, s, strict=True))
    total += sum(value * s[i] * s[k] for i, k, value in couplers)
    return total


def bqm_objective_value(
    bits: list[int] | tuple[int, ...],
    linear: list[float] | tuple[float, ...],
    quadratic: list[tuple[int, int, float]] | tuple[tuple[int, int, float], ...],
    offset: float = 0.0,
) -> float:
    x = tuple(int(value) for value in bits)
    if len(x) != len(linear):
        raise ValueError("BQM vector length must match linear coefficient count")
    total = float(offset) + sum(float(coef) * bit for coef, bit in zip(linear, x, strict=True))
    total += sum(float(value) * x[i] * x[j] for i, j, value in quadratic)
    return total
