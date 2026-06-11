"""False-discovery, overfit, and rank-instability controls."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .cost_model import numeric
from .normalization import clamp, round6


def cluster_id(row: dict[str, Any]) -> str:
    formula_family = str(row.get("formula_family") or "GENERAL_REPLAY_PAPER_FORMULA_FAMILY")
    condition_id = str(row.get("condition_fingerprint_id") or "CONDITION_TERMINAL_BY_NATURE")
    return f"PR166_SM_SCORE_CLUSTER::{formula_family}::{condition_id}"


def cluster_counts(prior_rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(cluster_id(row) for row in prior_rows)


def risk_controls(
    *,
    row: dict[str, Any],
    prior_fd_row: dict[str, Any],
    related_trials: int,
    near_duplicate_trials: int,
    scenario_count: int,
    cost_drag_ratio: float,
    latency_drag_ratio: float,
    refreshed_rank_percentile: float,
) -> dict[str, Any]:
    sample_depth = clamp(numeric(prior_fd_row, "evidence_count", 1.0) / 5.0)
    base_fd = clamp(numeric(prior_fd_row, "false_discovery_penalty", 0.35))
    duplicate_penalty = clamp((near_duplicate_trials - 1) / 25.0)
    sensitivity = clamp((cost_drag_ratio / 2.0) + latency_drag_ratio)
    singleton_penalty = 0.2 if related_trials <= 1 and refreshed_rank_percentile >= 0.95 else 0.0
    false_discovery = clamp((0.45 * base_fd) + (0.20 * duplicate_penalty) + (0.20 * (1 - sample_depth)) + (0.15 * sensitivity) + singleton_penalty)
    overfit = clamp((0.35 * (1 - sample_depth)) + (0.30 * duplicate_penalty) + (0.25 * sensitivity) + (0.10 if scenario_count <= 1 else 0.0))
    rank_instability = clamp(abs(0.5 - refreshed_rank_percentile) * 0.35 + sensitivity * 0.45 + duplicate_penalty * 0.20)
    return {
        "num_related_trials": related_trials,
        "num_near_duplicate_trials": near_duplicate_trials,
        "scenario_count": scenario_count,
        "effective_independent_trial_count": max(1, related_trials - int(near_duplicate_trials * 0.5)),
        "sample_depth_score": round6(sample_depth),
        "false_discovery_risk_adjustment": round6(false_discovery),
        "overfit_risk_adjustment": round6(overfit),
        "rank_instability_adjustment": round6(rank_instability),
        "rank_stability_score": round6(1 - rank_instability),
        "reject_as_miracle_singleton_flag": bool(singleton_penalty > 0),
    }
