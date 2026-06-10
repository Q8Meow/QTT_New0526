"""Computable formula templates for replay/paper candidate actions."""

from __future__ import annotations

FORMULA_TEMPLATES = {
    "implied_yes_probability_mid": "midpoint(best_yes_bid, best_yes_ask)",
    "implied_no_probability_mid": "midpoint(best_no_bid, best_no_ask)",
    "yes_expected_value": "model_probability_yes - effective_yes_price",
    "no_expected_value": "model_probability_no - effective_no_price",
    "fee_adjusted_edge": "gross_edge - estimated_fee_rate - fixed_fee_component",
    "slippage_adjusted_edge": "fee_adjusted_edge - estimated_slippage",
    "tca_adjusted_edge": "gross_edge - fee_component - slippage_component - adverse_selection_proxy",
    "latency_adjusted_edge": "tca_adjusted_edge - latency_penalty",
    "liquidity_fragility_score": "f(spread, depth, turnover, stale_quote_age, order_size_ratio)",
    "scenario_memory_adjusted_priority": (
        "base_priority + positive_memory_boost - negative_memory_penalty - fragile_watchlist_penalty"
    ),
    "fractional_kelly_research_sizing_candidate": "clamp(edge / variance_proxy, min_size, max_research_size)",
    "calibration_error_candidate": "abs(predicted_probability - observed_frequency_proxy)",
    "cross_venue_discrepancy_candidate": (
        "abs(normalized_probability_a - normalized_probability_b) - transfer_cost_proxy - settlement_mismatch_penalty"
    ),
    "retest_priority_score": "weighted deterministic replay/paper priority from PR165 score and PR165-B memory fields",
}


def template_record(template_id: str) -> dict[str, str]:
    return {
        "formula_template_id": template_id,
        "expression_text": FORMULA_TEMPLATES[template_id],
        "authority_boundary_ref": "PR165_C_AUTHORITY_BOUNDARY::REPLAY_PAPER_MEMORY_CONSUMER_ONLY",
    }
