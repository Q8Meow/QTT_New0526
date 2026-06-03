"""Coefficient validation helpers."""

from __future__ import annotations

import math
from typing import Any


def validate_numeric_coefficients(values: list[float] | tuple[float, ...]) -> dict[str, Any]:
    finite = all(math.isfinite(float(value)) for value in values)
    return {
        "coefficient_count": len(values),
        "finite_coefficients_flag": finite,
        "nonempty_coefficients_flag": bool(values),
        "coefficient_validation_status": "PASS" if finite and values else "FAIL",
    }


def flatten_qubo_coefficients(q_matrix: list[list[float]] | tuple[tuple[float, ...], ...]) -> list[float]:
    return [float(value) for row in q_matrix for value in row]
