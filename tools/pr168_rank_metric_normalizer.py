#!/usr/bin/env python3
"""Deterministic score normalization helpers for PR168-RANK."""

from __future__ import annotations

from math import isfinite
from statistics import median
from typing import Iterable


def robust_minmax(values: Iterable[float]) -> dict[float, float]:
    clean = [float(value) for value in values if isfinite(float(value))]
    if not clean:
        return {}
    low = min(clean)
    high = max(clean)
    if abs(high - low) < 1e-12:
        return {value: 0.0 for value in clean}
    return {value: round((value - low) / (high - low), 10) for value in clean}


def median_mad_score(value: float, population: Iterable[float]) -> float:
    clean = [float(item) for item in population if isfinite(float(item))]
    if not clean:
        return 0.0
    med = median(clean)
    deviations = [abs(item - med) for item in clean]
    mad = median(deviations) or 1.0
    return round((float(value) - med) / mad, 10)
