"""QKU prioritization feature handoff records without scoring or ranking."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_qku_prioritization_handoff(
    *,
    index: int,
    row_resolution: dict[str, Any],
    expected_value: float,
    edge_after_cost: float,
    fill_probability: float,
    orderbook_depth: float,
    latency_bucket: str,
    capital_lockup: float,
    quantum_refs: list[str],
) -> dict[str, Any]:
    return {
        "qku_prioritization_feature_handoff_ref": plain_ref("QKU_PRIORITY_FEATURE_HANDOFF", index),
        "candidate_packet_id": row_resolution["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids", []),
        "formulation_refs": [row_resolution.get("formulation_ref")] if row_resolution.get("formulation_ref") else [],
        "formula_refs": [row_resolution.get("callable_ref")] if row_resolution.get("callable_ref") else [],
        "algorithm_refs": ["PR163_PAPER_DECISION_ALGORITHM_V1"],
        "parameter_stack_refs_if_present": [],
        "expected_value_ref_or_value": expected_value,
        "edge_after_fees_slippage_spread": edge_after_cost,
        "fill_probability_candidate": fill_probability,
        "orderbook_depth_ref_or_value": orderbook_depth,
        "latency_sensitivity_bucket": latency_bucket,
        "capital_lockup_estimate": capital_lockup,
        "drawdown_exposure_ref_or_value": 0.0,
        "event_exposure_ref_or_value": capital_lockup,
        "category_exposure_ref_or_value": capital_lockup,
        "venue_exposure_ref_or_value": capital_lockup,
        "settlement_risk_ref_or_value": "SYNTHETIC_FIXTURE_SETTLEMENT_RISK_CANDIDATE",
        "data_quality_tier": row_resolution.get("data_quality_tier", "DQ0_SYNTHETIC_TEST_ONLY"),
        "paper_capture_quality_status": "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE",
        "replay_result_placeholder_ref_only": plain_ref("REPLAY_RESULT_PLACEHOLDER_ONLY", index),
        "replay_result_created": False,
        "paper_result_created": False,
        "quantum_compatibility_status": "QUANTUM_COMPATIBLE" if quantum_refs else "CLASSICAL_ONLY_FOR_NOW",
        "quantum_advisory_refs": quantum_refs,
        "classical_comparator_delta_ref_or_value": "PR163_CLASSICAL_COMPARATOR_DELTA_CANDIDATE_ONLY",
        "owner_quantum_priority_status": "OWNER_QUANTUM_PRIORITY_ROUTE_PRESERVED" if quantum_refs else "NO_OWNER_QUANTUM_PRIORITY_FOR_ROW",
        "downstream_pr163_b_paired_replay_paper_executor_ref": plain_ref("PR163B_HANDOFF", index),
        "downstream_pr164_review_provenance_ref": plain_ref("PR164_HANDOFF", index),
        "downstream_pr165_scoring_ranking_ref": plain_ref("PR165_HANDOFF", index),
        "no_score_created": True,
        "no_rank_created": True,
        "no_promotion_created": True,
        "no_profit_evidence": True,
        "no_live_authority": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
