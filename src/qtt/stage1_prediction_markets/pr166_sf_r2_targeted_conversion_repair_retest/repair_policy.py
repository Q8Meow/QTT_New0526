"""Scoring helpers for PR166-SF-R2 repair policy."""

from __future__ import annotations

from typing import Mapping


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def round6(value: float) -> float:
    return round(float(value), 6)


def repair_retest_score_v2(components: Mapping[str, float], weights: Mapping[str, float]) -> float:
    return round6(sum(float(components.get(name, 0.0)) * weight for name, weight in weights.items()))
