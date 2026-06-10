"""Deterministic score normalization helpers for PR165-D."""

from __future__ import annotations

from typing import Iterable


def clamp_0_1(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return round(value, 6)


def score_points(value: object, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return clamp_0_1(numeric / 100.0)


def positive_rank_strength(rank: object, total: int) -> float:
    try:
        numeric = int(rank)
    except (TypeError, ValueError):
        return 0.5
    if total <= 1:
        return 1.0
    return clamp_0_1(1.0 - ((numeric - 1) / (total - 1)))


def bounded_numeric(value: object, *, lower: float, upper: float, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    if upper <= lower:
        return 0.5
    return clamp_0_1((numeric - lower) / (upper - lower))


def inverse_score_points(value: object, default: float = 0.0) -> float:
    return clamp_0_1(1.0 - score_points(value, default=default))


def bucketize(value: float, *, low: float, high: float) -> str:
    if value <= low:
        return "LOW"
    if value >= high:
        return "HIGH"
    return "MEDIUM"


def percentile_rank(values: Iterable[float], value: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.5
    below_or_equal = sum(1 for item in ordered if item <= value)
    return clamp_0_1(below_or_equal / len(ordered))
