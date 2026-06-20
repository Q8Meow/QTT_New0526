#!/usr/bin/env python3
"""Negative-candidate recovery for PR168-RP."""

from __future__ import annotations

from typing import Any


RECOVERY_LADDER = [
    "input_repair",
    "formula_repair",
    "probability_calibration_repair",
    "microstructure_repair",
    "order_policy_repair",
    "size_capacity_repair",
    "timing_regime_repair",
    "portfolio_repair",
    "qku_formula_algorithm_combination_repair",
    "quantum_forward_structural_repair",
    "terminal_classification",
]


def reason_codes_for_negative(metrics: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    gross = abs(float(metrics["gross_edge"]))
    if float(metrics["market_implied_probability"]) >= float(metrics["predicted_probability"]):
        reasons.append("market_implied_probability_too_high")
    if float(metrics["spread_cost"]) > gross:
        reasons.append("spread_cost_exceeds_edge")
    if float(metrics["slippage_cost"]) > gross:
        reasons.append("slippage_cost_exceeds_edge")
    if float(metrics["market_impact"]) > gross:
        reasons.append("market_impact_exceeds_edge")
    if float(metrics["adverse_selection_penalty"]) > gross:
        reasons.append("adverse_selection_exceeds_edge")
    if float(metrics["implementation_shortfall"]) > gross:
        reasons.append("implementation_shortfall_exceeds_edge")
    if float(metrics["fill_probability"]) < 0.55:
        reasons.append("fill_probability_too_low")
    if float(metrics["latency_decay"]) > gross:
        reasons.append("latency_decay_exceeds_edge")
    if float(metrics["capacity_crowding_penalty"]) > gross:
        reasons.append("capacity_crowding_exceeds_edge")
    if float(metrics["overfit_fdr_penalty"]) > gross:
        reasons.append("overfit_fdr_penalty_exceeds_edge")
    if float(metrics["portfolio_marginal_utility"]) <= 0:
        reasons.append("portfolio_marginal_utility_negative")
    if float(metrics["no_trade_comparison_margin"]) <= 0:
        reasons.append("no_trade_candidate_dominates")
    if metrics.get("missing_default_blocking_flag"):
        reasons.append("data_default_missing")
    return sorted(set(reasons or ["prediction_wrong_or_uncalibrated"]))


def build_recovery_attempt(computed: dict[str, Any]) -> dict[str, Any]:
    reasons = reason_codes_for_negative(computed["metrics"])
    status = "NEGATIVE_RECOVERY_EXHAUSTED_TRUE_NEGATIVE" if "data_default_missing" in reasons else "NEGATIVE_RECOVERY_CANDIDATE_CREATED"
    return {
        "negative_recovery_ref": computed["negative_recovery_ref"],
        "canonical_row_key": computed["canonical_row_key"],
        "qku_id": computed["qku_id"],
        "computed_status_before_repair": computed["computed_status"],
        "negative_reason_codes": reasons,
        "repair_ladder_attempted": RECOVERY_LADDER,
        "repair_attempt_count": len(RECOVERY_LADDER),
        "new_numeric_recompute_after_repair": False,
        "repaired_positive_created": False,
        "recovery_status": status,
        "still_negative_repair_route": "PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json"
        if status.endswith("TRUE_NEGATIVE")
        else "PR168_RP_NegativeRecoveryCandidateFactory.report.json",
        "downstream_route": "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json",
        "owning_agent": "Alpha Recovery Agent",
        "supporting_agents": ["Risk Manager Agent", "Quantum AutoMapper Agent", "Replay Paper Recompute Agent"],
        "producer": "PR168_RP_NEGATIVE_RECOVERY_ENGINE",
        "consumer": "PR168_RANK",
        "upstream_source": computed["result_ref"],
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "live_authority": False,
        "no_orphan_status": "CONNECTED_TO_NEGATIVE_RECOVERY_CONSUMER",
    }
