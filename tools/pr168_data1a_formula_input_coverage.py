#!/usr/bin/env python3
"""Formula input coverage matrix for PR168-DATA1A."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


FORMULA_REQUIREMENTS = {
    "PR168_GFP_FORMULA_MARKET_IMPLIED_PROBABILITY": ["market_price", "contract_terms", "fee_adjustment"],
    "PR168_GFP_FORMULA_GROSS_EDGE": ["market_implied_probability", "predicted_probability"],
    "PR168_GFP_FORMULA_SPREAD_COST": ["bid", "ask"],
    "PR168_GFP_FORMULA_EXPLICIT_FEE_COST": ["fee_rate", "quantity"],
    "PR168_GFP_FORMULA_SLIPPAGE_COST": ["orderbook_depth", "quantity"],
    "PR168_GFP_FORMULA_TCA_DECOMPOSITION": ["spread_cost", "fee_rate", "slippage_cost", "latency_ms"],
    "PR168_GFP_FORMULA_CAPACITY_CROWDING": ["orderbook_depth", "volume"],
    "PR168_GFP_FORMULA_OVERFIT_FDR": ["trial_family_id", "sample_window"],
    "PR168_GFP_FORMULA_EXECUTION_ADJUSTED_EDGE": ["gross_edge", "tca_cost", "fill_probability"],
    "PR168_GFP_FORMULA_NET_EXPECTED_PNL": ["expected_value", "costs"],
    "PR168_GFP_FORMULA_LOWER_CONFIDENCE_BOUND": ["edge_sample", "variance"],
    "PR168_GFP_FORMULA_QUBO_OBJECTIVE": ["alpha_coefficient", "cost_coefficient", "constraints", "penalty_scaling"],
}


def _available_inputs(inventory: dict[str, Any]) -> set[str]:
    inputs = {"contract_terms", "market_price", "bid", "ask", "orderbook_depth", "volume", "sample_window"}
    if inventory.get("total_historical_trade_row_count", 0) or inventory.get("total_price_history_or_candle_point_count", 0):
        inputs.add("market_implied_probability")
        inputs.add("edge_sample")
        inputs.add("variance")
    if inventory.get("total_forward_l2_row_count", 0):
        inputs.add("fill_probability")
        inputs.add("latency_ms")
    if inventory.get("polymarket_unique_token_or_asset_count", 0):
        inputs.add("fee_rate")
    return inputs


def build_formula_input_coverage(inventory: dict[str, Any], qku_rows: list[dict[str, Any]], created_at_utc: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    available = _available_inputs(inventory)
    rows: list[dict[str, Any]] = []
    for index, (formula_id, required) in enumerate(FORMULA_REQUIREMENTS.items(), start=1):
        present = sorted(set(required) & available)
        missing = sorted(set(required) - available)
        if not missing:
            state = "READY"
        elif present:
            state = "PARTIAL"
        else:
            state = "MISSING"
        rows.append(
            {
                "formula_input_coverage_row_id": f"formula_input_coverage_{index:05d}",
                "formula_id": formula_id,
                "required_inputs": required,
                "DATA1_available_inputs": present,
                "remaining_missing_inputs": missing,
                "coverage_state": state,
                "coverage_rate": round(len(present) / len(required), 6),
                "GFP2R_consumption_allowed_flag": state == "READY",
                "GFP2R_repair_required_flag": state != "READY",
                "source_rows": [row["qku_unblock_row_id"] for row in qku_rows[:5]],
                "created_at_utc": created_at_utc,
                **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_NormalizedMarketDataFeatureRegistry"))]),
            }
        )
    coverage_rate = round(sum(row["coverage_rate"] for row in rows) / len(rows), 6) if rows else 0.0
    summary = {
        "formula_input_coverage_rate": coverage_rate,
        "formula_input_ready_count": len([row for row in rows if row["coverage_state"] == "READY"]),
        "formula_input_partial_count": len([row for row in rows if row["coverage_state"] == "PARTIAL"]),
        "formula_input_missing_count": len([row for row in rows if row["coverage_state"] == "MISSING"]),
        "GFP2R_exact_formula_proof_consumption_allowed_count": len([row for row in rows if row["GFP2R_consumption_allowed_flag"]]),
        "GFP2R_formula_repair_required_count": len([row for row in rows if row["GFP2R_repair_required_flag"]]),
        **route_defaults("formula", data1_refs=[generated_ref(report_path("PR168_DATA1_NormalizedMarketDataFeatureRegistry"))]),
    }
    return summary, rows
