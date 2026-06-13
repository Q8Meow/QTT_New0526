"""Deterministic PR166-SM2 score formulas."""

from __future__ import annotations

from . import constants as c


def round6(value: float) -> float:
    return round(float(value), 6)


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return min(upper, max(lower, float(value)))


def weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    return round6(sum(float(components.get(key, 0.0)) * weight for key, weight in weights.items()))


def score_memory_refresh_score_v2(components: dict[str, float]) -> float:
    return weighted_score(components, c.SCORE_WEIGHTS)


def positive_expansion_priority_v2(components: dict[str, float]) -> float:
    return weighted_score(components, c.POSITIVE_EXPANSION_WEIGHTS)


def convertible_negative_priority_v2(components: dict[str, float]) -> float:
    return weighted_score(components, c.CONVERTIBLE_NEGATIVE_WEIGHTS)
