#!/usr/bin/env python3
"""Edge attribution rows for PR168-RP."""

from __future__ import annotations

from typing import Any


def build_edge_attribution(computed: dict[str, Any]) -> dict[str, Any]:
    metrics = computed["metrics"]
    return {
        "edge_attribution_ref": computed["edge_attribution_ref"],
        "canonical_row_key": computed["canonical_row_key"],
        "qku_id": computed["qku_id"],
        "raw_model_edge_component": metrics["gross_edge"],
        "calibration_adjustment_component": metrics.get("probability_calibration_error"),
        "market_implied_probability_component": metrics["market_implied_probability"],
        "microstructure_component": -metrics["total_tca"],
        "order_timing_component": -metrics["latency_decay"],
        "order_policy_component": computed.get("best_order_policy_ref"),
        "spread_capture_or_avoidance_component": -metrics["spread_cost"],
        "latency_component": -metrics["latency_decay"],
        "capacity_component": -metrics["capacity_crowding_penalty"],
        "portfolio_marginal_utility_component": metrics["portfolio_marginal_utility"],
        "quantum_combinatorial_selection_component": computed["quantum_structural_readiness"],
        "execution_cost_reduction_component": -metrics["total_tca"],
        "no_trade_comparison_component": metrics["no_trade_comparison_margin"],
        "overfit_penalty_component": -metrics["overfit_fdr_penalty"],
        "final_execution_adjusted_edge": metrics["execution_adjusted_edge"],
        "final_fill_adjusted_expected_pnl": metrics["fill_adjusted_expected_pnl"],
        "producer": "PR168_RP_EDGE_ATTRIBUTION",
        "consumer": "PR168_RANK",
        "upstream_source": computed["result_ref"],
        "downstream_route": "PR168_RP_EdgeAttribution.report.json",
        "owning_agent": "Risk Manager Agent",
        "no_orphan_status": "CONNECTED_TO_EDGE_ATTRIBUTION_CONSUMER",
    }
