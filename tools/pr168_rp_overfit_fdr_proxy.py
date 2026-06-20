#!/usr/bin/env python3
"""Deterministic overfit/FDR proxy for PR168-RP."""

from __future__ import annotations

from typing import Any


def compute_overfit_fdr_proxy(row: dict[str, Any]) -> dict[str, Any]:
    repair_needed = bool(row.get("repair_needed_before_retest"))
    repeated_test_count = int(float(row.get("near_duplicate_cluster_size", 1)))
    order_policy_trial_count = 7
    scenario_ladder_trial_count = 13
    proxy_penalty = float(row["overfit_risk_adjustment"])
    return {
        "family_trial_count": 35,
        "candidate_trial_count": int(float(row.get("pr165_d2_rank", 1))),
        "repeated_test_count": repeated_test_count,
        "parameter_sweep_count": max(1, repeated_test_count),
        "repair_attempt_count": 1 if repair_needed else 0,
        "qku_combination_trial_count": int(float(row.get("near_duplicate_cluster_size", 1))),
        "order_policy_trial_count": order_policy_trial_count,
        "scenario_ladder_trial_count": scenario_ladder_trial_count,
        "replay_paper_disagreement": bool(row.get("repair_needed_before_retest")),
        "regime_instability_score": float(row["rank_instability_adjustment"]),
        "weak_sample_size_flag": row.get("result_confidence_score", 0) < 0.55,
        "post_selection_bias_flag": True,
        "overfit_fdr_penalty": proxy_penalty,
        "overfit_disqualification_reason": "data_default_missing" if repair_needed else None,
        "formal_bh_or_dsr_claimed": False,
    }
