"""Constraint feasibility checks for tiny binary smoke problems."""

from __future__ import annotations

from typing import Any


def linear_constraint_value(bits: list[int] | tuple[int, ...], coefficients: list[float] | tuple[float, ...]) -> float:
    if len(bits) != len(coefficients):
        raise ValueError("constraint coefficient count must match assignment")
    return sum(float(coef) * int(bit) for coef, bit in zip(coefficients, bits, strict=True))


def check_linear_constraint(
    bits: list[int] | tuple[int, ...],
    coefficients: list[float] | tuple[float, ...],
    sense: str,
    rhs: float,
    *,
    tolerance: float = 1e-9,
) -> dict[str, Any]:
    value = linear_constraint_value(bits, coefficients)
    if sense == "<=":
        feasible = value <= float(rhs) + tolerance
    elif sense == ">=":
        feasible = value >= float(rhs) - tolerance
    elif sense == "==":
        feasible = abs(value - float(rhs)) <= tolerance
    else:
        raise ValueError("unsupported constraint sense")
    return {
        "lhs_value": value,
        "sense": sense,
        "rhs": float(rhs),
        "feasible_flag": feasible,
        "violation": max(0.0, value - float(rhs)) if sense == "<=" else abs(value - float(rhs)),
    }
