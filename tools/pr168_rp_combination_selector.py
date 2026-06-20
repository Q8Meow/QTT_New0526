#!/usr/bin/env python3
"""QKU and order-policy combination selector for PR168-RP."""

from __future__ import annotations

from typing import Any


def combination_row(computed: dict[str, Any]) -> dict[str, Any]:
    metrics = computed["metrics"]
    source = computed["source_rows"]["ranking"]
    return {
        "combination_id": source.get("combination_id"),
        "qku_refs": [computed["qku_id"]],
        "formula_refs": computed.get("formula_ids", []),
        "algorithm_refs": [source.get("algorithm_id")],
        "parameter_stack_refs": [source.get("parameter_stack_id")],
        "order_policy_refs": ["PR168_RP_OrderPolicyCandidateRanking.report.json"],
        "market_scope": source.get("market_scope"),
        "venue_scope": source.get("venue"),
        "event_scope": source.get("prediction_market_event_type"),
        "source_lane": "REPLAY_PAPER_SELECTION_CANDIDATE_LANE",
        "execution_adjusted_edge": metrics["execution_adjusted_edge"],
        "fill_adjusted_expected_pnl": metrics["fill_adjusted_expected_pnl"],
        "lower_confidence_bound_edge": metrics["lower_confidence_bound_edge"],
        "no_trade_comparison_margin": metrics["no_trade_comparison_margin"],
        "portfolio_marginal_utility": metrics["portfolio_marginal_utility"],
        "overfit_fdr_penalty": metrics["overfit_fdr_penalty"],
        "capacity_usage": metrics["capacity_usage"],
        "crowding_score": metrics["crowding_score"],
        "quantum_structural_readiness": computed["quantum_structural_readiness"],
        "calibration_status": metrics["calibration_status"],
        "TCA_status": "TCA_COMPUTED_FROM_REPO_INPUTS",
        "replay_paper_status": computed["evidence_tier"],
        "pretrade_simulation_status": "PRETRADE_SIMULATION_CANDIDATE_CREATED",
        "downstream_route": "PR168_RP_MarginalUtilitySelectionResults.report.json",
        "producer": "PR168_RP_COMBINATION_SELECTOR",
        "consumer": "PR168_RANK",
        "upstream_source": computed["result_ref"],
        "owning_agent": "Portfolio/Risk Agent",
        "no_orphan_status": "CONNECTED_TO_COMBINATION_SELECTION_CONSUMER",
    }
