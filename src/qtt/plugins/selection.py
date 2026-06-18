"""Selection scoring helpers for nonlive PR162E ranking."""

from __future__ import annotations


def lower_confidence_bound(edge: float, uncertainty_penalty: float) -> float:
    return round(float(edge) - float(uncertainty_penalty), 6)


def repair_roi(expected_repair_value: float, expected_repair_cost: float) -> float:
    cost = max(float(expected_repair_cost), 0.000001)
    return round(float(expected_repair_value) / cost, 6)
