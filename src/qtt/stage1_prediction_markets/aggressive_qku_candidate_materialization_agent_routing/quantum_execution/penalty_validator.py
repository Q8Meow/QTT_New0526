"""Penalty validation helpers."""

from __future__ import annotations

from typing import Any


def penalty_value(violation: float, penalty_lambda: float) -> float:
    if penalty_lambda < 0:
        raise ValueError("penalty_lambda must be non-negative")
    return float(penalty_lambda) * float(violation) ** 2


def penalty_validation_record(violation: float, penalty_lambda: float) -> dict[str, Any]:
    return {
        "violation": float(violation),
        "penalty_lambda": float(penalty_lambda),
        "penalty_value": penalty_value(violation, penalty_lambda),
        "penalty_valid_flag": penalty_lambda >= 0,
    }
