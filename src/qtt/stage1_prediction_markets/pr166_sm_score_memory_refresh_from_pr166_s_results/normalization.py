"""Deterministic score normalization helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def round6(value: float) -> float:
    return round(float(value), 6)


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def winsor_caps(values: Iterable[float], min_count: int = 20) -> tuple[float, float, str]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0, 1.0, "FALLBACK_CAPS_FROM_EMPTY_VALUE_SET_MATERIALIZATION_ACTION"
    if len(ordered) < min_count:
        return ordered[0], ordered[-1], "FALLBACK_CAPS_FROM_AVAILABLE_PRIOR_SCORE_RANGE"
    return percentile(ordered, 0.01), percentile(ordered, 0.99), "PERCENTILE_CAPS_01_99"


def normalize_signed(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    capped = max(low, min(high, float(value)))
    return clamp((capped - low) / (high - low))


def rank_normalize_by_group(items: list[dict[str, object]], group_key: str, value_key: str) -> dict[str, float]:
    groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for item in items:
        groups[str(item[group_key])].append((str(item["candidate_packet_id"]), float(item[value_key])))
    normalized: dict[str, float] = {}
    for group_rows in groups.values():
        ordered = sorted(group_rows, key=lambda pair: (pair[1], pair[0]))
        if len(ordered) == 1:
            normalized[ordered[0][0]] = 1.0
            continue
        denom = len(ordered) - 1
        for rank, (candidate_id, _value) in enumerate(ordered):
            normalized[candidate_id] = round6(rank / denom)
    return normalized
