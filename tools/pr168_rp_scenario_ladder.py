#!/usr/bin/env python3
"""Scenario ladder for PR168-RP pretrade candidates."""

from __future__ import annotations

from typing import Any


SCENARIOS = [
    "base_case",
    "best_case",
    "worst_case",
    "spread_widening_case",
    "partial_fill_case",
    "no_fill_case",
    "latency_stale_book_case",
    "adverse_selection_case",
    "liquidity_disappears_case",
    "news_shock_case",
    "probability_reversion_case",
    "correlated_event_loss_case",
    "settlement_delay_case",
    "fee_model_error_case",
]


def build_scenario_ladder(computed: dict[str, Any]) -> dict[str, Any]:
    metrics = computed["metrics"]
    base = float(metrics["fill_adjusted_expected_pnl"])
    stress = abs(float(metrics["total_tca"])) + abs(float(metrics["expected_shortfall_cvar"]))
    cases = []
    for index, scenario in enumerate(SCENARIOS, start=1):
        expected = base if scenario == "base_case" else base - stress * index / len(SCENARIOS)
        cases.append(
            {
                "scenario_name": scenario,
                "expected_net_pnl": round(expected, 10),
                "lower_confidence_bound_edge": metrics["lower_confidence_bound_edge"],
                "worst_case_loss": round(abs(min(expected, 0.0)) + stress, 10),
                "expected_shortfall_cvar": metrics["expected_shortfall_cvar"],
                "no_trade_comparison_margin": round(expected, 10),
                "scenario_pass": False,
                "failure_reason_code": "MISSING_DEFAULT_THRESHOLD" if metrics.get("missing_default_blocking_flag") else "NO_TRADE_DOMINATES",
            }
        )
    return {
        "scenario_ladder_ref": f"PR168_RP_SCENARIO::{computed['result_ref']}",
        "canonical_row_key": computed["canonical_row_key"],
        "qku_id": computed["qku_id"],
        "scenario_cases": cases,
        "scenario_ladder_pass": False,
        "downstream_route": "PR168_RP_ScenarioFailureRepairQueue.report.json",
        "owning_agent": "Risk Manager Agent",
        "producer": "PR168_RP_SCENARIO_LADDER",
        "consumer": "PR168_RANK",
        "upstream_source": computed["result_ref"],
        "no_orphan_status": "CONNECTED_TO_SCENARIO_CONSUMER",
    }
