"""Capacity, crowding, and correlation controls."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .cost_model import numeric
from .normalization import clamp, round6


def capacity_bucket(score: float) -> str:
    if score >= 0.75:
        return "HIGH_CAPACITY"
    if score >= 0.45:
        return "MEDIUM_CAPACITY"
    return "LOW_CAPACITY"


def correlation_cluster_id(row: dict[str, Any]) -> str:
    combination = str(row.get("combination_fingerprint_id") or row.get("combination_id") or "COMBINATION_TERMINAL_BY_NATURE")
    formula = str(row.get("formula_family") or "GENERAL_REPLAY_PAPER_FORMULA_FAMILY")
    return f"PR166_SM_CORRELATION_CLUSTER::{combination}::{formula}"


def cluster_counter(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(correlation_cluster_id(row) for row in rows)


def capacity_metrics(
    *,
    cost_drag_ratio: float,
    liquidity_drag_ratio: float,
    marginal_utility_row: dict[str, Any],
    cluster_size: int,
    refreshed_rank_percentile: float,
) -> dict[str, Any]:
    marginal = clamp(numeric(marginal_utility_row, "marginal_candidate_utility", 0.5))
    capacity_score = clamp((0.55 * marginal) + (0.25 * (1 - liquidity_drag_ratio)) + (0.20 * (1 - min(cost_drag_ratio, 1.0))))
    crowding_penalty = clamp(max(0, cluster_size - 1) / 30.0 + (0.15 if refreshed_rank_percentile < 0.5 else 0.0))
    correlation_penalty = clamp(max(0, cluster_size - 1) / 40.0)
    return {
        "capacity_score": round6(capacity_score),
        "capacity_bucket": capacity_bucket(capacity_score),
        "crowding_penalty": round6(crowding_penalty),
        "correlation_cluster_penalty": round6(correlation_penalty),
        "marginal_utility_score": round6(marginal),
        "overlap_with_existing_winners": max(0, cluster_size - 1),
    }
