#!/usr/bin/env python3
"""Negative-to-positive recovery ladder routing for PR168-GFP2."""

from __future__ import annotations

from typing import Any


RECOVERY_DIMENSIONS = (
    "wrong_side_or_inverted_payoff",
    "uncalibrated_probability",
    "stale_market_snapshot",
    "missing_resolution_or_settlement_semantics",
    "fee_model_gap_or_overestimate",
    "slippage_model_gap_or_overestimate",
    "fill_probability_gap_or_overestimate",
    "latency_decay_gap_or_overestimate",
    "capacity_or_depth_gap",
    "entry_price_too_aggressive",
    "order_size_too_large",
    "order_policy_wrong_for_book_state",
    "spread_regime_too_wide",
    "liquidity_regime_too_thin",
    "time_to_resolution_unsuitable",
    "market_family_correlation_penalty_excessive",
    "overfit_or_false_discovery_penalty_excessive",
    "portfolio_utility_negative_due_concentration",
    "regime_condition_mismatch",
    "quantum_mapping_missing_coefficients_or_constraints",
    "classical_baseline_missing_or_weak",
    "candidate_source_unaccepted",
    "synthetic_proxy_or_internal_evidence_only",
)

RECOVERY_ACTIONS = (
    "data_repair",
    "formula_repair",
    "calibration_repair",
    "cost_repair",
    "execution_policy_repair",
    "capacity_crowding_repair",
    "regime_repair",
    "portfolio_repair",
    "overfit_fdr_repair",
    "quantum_forward_repair",
    "combination_repair",
    "retest_routing",
)


def recovery_opportunity_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in universe_rows:
        rows.append(
            {
                "canonical_row_key": row["canonical_row_key"],
                "qku_id": row["qku_id"],
                "old_classification": row["old_classification"],
                "recovery_eligibility_state": row["recovery_eligibility_state"],
                "diagnosis_dimensions": list(_dimensions_for_row(row)),
                "recovery_action_refs": ["PR168_GFP2_NegativeCandidateRepairLadderQueue.report.json"],
                "forced_positive_flag": False,
                "real_positive_claim_allowed_flag": False,
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "agent_owner": "Alpha Recovery Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def repair_ladder_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in universe_rows:
        rows.append(
            {
                "repair_queue_id": f"{row['canonical_row_key']}::RECOVERY_LADDER",
                "canonical_row_key": row["canonical_row_key"],
                "qku_id": row["qku_id"],
                "recovery_action_ladder": list(RECOVERY_ACTIONS),
                "repair_status": "PENDING_PR168_RP2_REAL_DATA_RECOMPUTE",
                "forced_positive_flag": False,
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "agent_owner": "Alpha Recovery Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def recovery_dimension_rows() -> list[dict[str, Any]]:
    return [
        {
            "recovery_dimension": dimension,
            "diagnosis_status": "REQUIRES_ACCEPTED_REAL_DATA_OR_BINDING_REPAIR",
            "may_recover_negative_to_positive_flag": True,
            "may_force_positive_without_proof_flag": False,
            "downstream_pr_refs": ["PR168-RP2"],
            "agent_owner": "Alpha Recovery Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for dimension in RECOVERY_DIMENSIONS
    ]


def _dimensions_for_row(row: dict[str, Any]) -> tuple[str, ...]:
    if row.get("prior_fake_negative_flag"):
        return (
            "synthetic_proxy_or_internal_evidence_only",
            "candidate_source_unaccepted",
            "fee_model_gap_or_overestimate",
            "slippage_model_gap_or_overestimate",
            "fill_probability_gap_or_overestimate",
            "latency_decay_gap_or_overestimate",
            "capacity_or_depth_gap",
        )
    return ("candidate_source_unaccepted", "missing_resolution_or_settlement_semantics", "classical_baseline_missing_or_weak")
