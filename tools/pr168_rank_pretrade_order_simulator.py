#!/usr/bin/env python3
"""Normalize PR168-RP pretrade rows into PR168-RANK simulated-order rows."""

from __future__ import annotations

from typing import Any

from tools.pr168_rank_evidence_model import score_components_from_pretrade, total_tca_from_pretrade
from tools.pr168_rank_report_writer import authority_flags


def build_simulated_orders(pretrade_rows: list[dict[str, Any]], stack_by_result: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(pretrade_rows, start=1):
        result_ref = _result_from_candidate(row)
        stack_id = stack_by_result.get(result_ref, f"PR168_RANK_STACK_GAP::{result_ref}")
        components = score_components_from_pretrade(row)
        rows.append(
            {
                "simulated_order_id": f"PR168_RANK_SIM_ORDER::{index:06d}",
                "source_pretrade_candidate_id": row.get("candidate_id"),
                "candidate_stack_id": stack_id,
                "side": row.get("side", "YES"),
                "order_type_candidate": row.get("order_type_candidate"),
                "limit_price_candidate": row.get("limit_price_candidate"),
                "quantity_candidate": row.get("quantity_candidate"),
                "notional_candidate": _round(float(row.get("expected_price", 0.0) or 0.0) * float(row.get("quantity_candidate", 0.0) or 0.0)),
                "time_in_force_candidate": row.get("time_in_force_candidate"),
                "expected_execution_price": row.get("expected_price"),
                "expected_fill_probability": row.get("expected_fill"),
                "expected_fill_time_ms": row.get("expected_latency"),
                "expected_latency_ms": row.get("expected_latency"),
                "explicit_fees": row.get("explicit_fee_cost"),
                "spread_crossing_cost": row.get("spread_cost"),
                "expected_slippage": row.get("slippage_cost"),
                "adverse_selection_cost": row.get("adverse_selection_penalty"),
                "market_impact_or_book_depth_cost": row.get("market_impact"),
                "failed_fill_or_cancel_cost": row.get("queue_nonfill_penalty"),
                "opportunity_cost_vs_no_trade": row.get("expected_unfilled_quantity"),
                "settlement_or_resolution_cost_proxy_when_applicable": 0.0,
                "capital_lock_cost": 0.0,
                "fill_adjusted_expected_pnl": components["fill_adjusted_expected_pnl"],
                "net_expected_pnl_candidate": components["net_expected_pnl_candidate"],
                "execution_adjusted_edge": components["execution_adjusted_edge"],
                "lower_confidence_bound_edge": components["lower_confidence_bound_edge"],
                "expected_shortfall_cvar_candidate": components["expected_shortfall_cvar_candidate"],
                "no_trade_comparison_margin": components["no_trade_comparison_margin"],
                "capacity_crowding_penalty": components["capacity_crowding_penalty"],
                "portfolio_marginal_utility": components["portfolio_marginal_utility"],
                "overfit_fdr_penalty": components["overfit_fdr_penalty"],
                "scenario_ladder_score": components["scenario_ladder_score"],
                "regime_stability_score": components["regime_stability_score"],
                "calibration_quality_score": components["calibration_quality_score"],
                "quantum_structural_readiness_score": components["quantum_structural_readiness_score"],
                "total_tca_cost": total_tca_from_pretrade(row),
                "mode_scope": row.get("mode", "REPLAY"),
                "decision_status": row.get("final_decision_status") or row.get("decision_status"),
                "champion_eligible": row.get("champion_eligible") is True,
                "champion_eligibility_blockers": row.get("champion_eligibility_blockers", []),
                "authority_boundary_flags": authority_flags(),
                "upstream_numeric_evidence_refs": [row.get("candidate_id")],
                "upstream_gap_refs": row.get("champion_eligibility_blockers", []),
            }
        )
    return rows


def _result_from_candidate(row: dict[str, Any]) -> str:
    text = str(row.get("candidate_id", ""))
    marker = "PR168_RP_RESULT::"
    if marker not in text:
        return text
    return marker + text.split(marker, 1)[1].split("::", 1)[0]


def _round(value: float) -> float:
    return round(float(value), 10)
