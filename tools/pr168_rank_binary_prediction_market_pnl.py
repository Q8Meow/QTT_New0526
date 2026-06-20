#!/usr/bin/env python3
"""Binary prediction-market PnL formulas for PR168-RANK."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


EPSILON = 1e-12


@dataclass(frozen=True)
class BinaryPnLInput:
    side: str
    calibrated_model_probability_yes: float
    execution_price: float
    order_quantity: float
    contract_size: float = 1.0
    explicit_fees_per_unit: float = 0.0
    spread_crossing_cost_per_unit: float = 0.0
    expected_slippage_per_unit: float = 0.0
    adverse_selection_cost_per_unit: float = 0.0
    latency_decay_cost_per_unit: float = 0.0
    market_impact_or_book_depth_cost_per_unit: float = 0.0
    settlement_or_resolution_cost_proxy_per_unit: float = 0.0
    capital_lock_cost_per_unit: float = 0.0
    fill_probability: float = 1.0
    unfilled_order_value: float = 0.0
    failed_fill_or_cancel_cost: float = 0.0
    opportunity_cost_vs_no_trade: float = 0.0
    lcb_win_probability: float | None = None
    conservative_total_tca_cost_per_unit: float | None = None
    uncertainty_penalty_per_unit: float = 0.0
    no_trade_value: float = 0.0
    compute_cost_proxy: float = 0.0
    risk_budget_usage_penalty: float = 0.0


def compute_binary_prediction_market_pnl(inputs: BinaryPnLInput) -> dict[str, float | str]:
    side = inputs.side.upper()
    if side not in {"YES", "NO"}:
        raise ValueError(f"unsupported binary side: {inputs.side}")
    _check_probability("calibrated_model_probability_yes", inputs.calibrated_model_probability_yes)
    _check_probability("fill_probability", inputs.fill_probability)
    if inputs.lcb_win_probability is not None:
        _check_probability("lcb_win_probability", inputs.lcb_win_probability)
    p_win = inputs.calibrated_model_probability_yes if side == "YES" else 1.0 - inputs.calibrated_model_probability_yes
    gross_ev_per_unit = p_win - inputs.execution_price
    total_tca_cost_per_unit = (
        inputs.explicit_fees_per_unit
        + inputs.spread_crossing_cost_per_unit
        + inputs.expected_slippage_per_unit
        + inputs.adverse_selection_cost_per_unit
        + inputs.latency_decay_cost_per_unit
        + inputs.market_impact_or_book_depth_cost_per_unit
        + inputs.settlement_or_resolution_cost_proxy_per_unit
        + inputs.capital_lock_cost_per_unit
    )
    net_expected_pnl_per_unit = gross_ev_per_unit - total_tca_cost_per_unit
    fill_adjusted_expected_pnl = (
        inputs.fill_probability * (net_expected_pnl_per_unit * inputs.order_quantity * inputs.contract_size)
        + (1.0 - inputs.fill_probability) * inputs.unfilled_order_value
        - inputs.failed_fill_or_cancel_cost
        - inputs.opportunity_cost_vs_no_trade
    )
    capital_at_risk = inputs.execution_price * inputs.order_quantity * inputs.contract_size
    lcb_win_probability = inputs.lcb_win_probability if inputs.lcb_win_probability is not None else p_win
    conservative_tca = (
        inputs.conservative_total_tca_cost_per_unit
        if inputs.conservative_total_tca_cost_per_unit is not None
        else total_tca_cost_per_unit
    )
    lower_confidence_bound_edge = (
        (lcb_win_probability - inputs.execution_price)
        - conservative_tca
        - inputs.uncertainty_penalty_per_unit
    )
    no_trade_comparison_margin = (
        fill_adjusted_expected_pnl
        - inputs.no_trade_value
        - inputs.compute_cost_proxy
        - inputs.risk_budget_usage_penalty
    )
    return {
        "side": side,
        "p_win": _round(p_win),
        "execution_price": _round(inputs.execution_price),
        "gross_ev_per_unit": _round(gross_ev_per_unit),
        "total_tca_cost_per_unit": _round(total_tca_cost_per_unit),
        "net_expected_pnl_per_unit": _round(net_expected_pnl_per_unit),
        "fill_adjusted_expected_pnl": _round(fill_adjusted_expected_pnl),
        "capital_at_risk": _round(capital_at_risk),
        "execution_adjusted_edge": _round(fill_adjusted_expected_pnl / max(capital_at_risk, EPSILON)),
        "lower_confidence_bound_edge": _round(lower_confidence_bound_edge),
        "no_trade_comparison_margin": _round(no_trade_comparison_margin),
    }


def _check_probability(label: str, value: float) -> None:
    if not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{label} must be a finite probability")


def _round(value: float) -> float:
    return round(float(value), 10)
