"""Execution-adjusted simulation rank preview."""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from .models import dec, score

DEFAULT_WEIGHTS = {
    "w_net": Decimal("0.25"),
    "w_lcb": Decimal("0.18"),
    "w_notrade": Decimal("0.12"),
    "w_fill": Decimal("0.10"),
    "w_scenario": Decimal("0.10"),
    "w_portfolio": Decimal("0.10"),
    "w_tca": Decimal("0.06"),
    "w_latency": Decimal("0.03"),
    "w_capacity": Decimal("0.03"),
    "w_fdr": Decimal("0.02"),
    "w_calibration": Decimal("0.01"),
}


def _norm(value: Decimal) -> Decimal:
    return value / (Decimal("1") + value.copy_abs())


def simulation_rank_score(metrics: Mapping[str, Decimal | str | int], weights: Mapping[str, Decimal] | None = None) -> Decimal:
    w = dict(DEFAULT_WEIGHTS if weights is None else weights)
    positive = (
        w["w_net"] * _norm(dec(metrics.get("net_expected_pnl_cash", 0)))
        + w["w_lcb"] * _norm(dec(metrics.get("lower_confidence_bound_pnl_cash", 0)))
        + w["w_notrade"] * _norm(dec(metrics.get("no_trade_margin_cash", 0)))
        + w["w_fill"] * dec(metrics.get("fill_probability", 0))
        + w["w_scenario"] * dec(metrics.get("scenario_robustness_score", 0))
        + w["w_portfolio"] * _norm(dec(metrics.get("portfolio_marginal_utility_cash", 0)))
    )
    negative = (
        w["w_tca"] * _norm(dec(metrics.get("TCA_total_cash", 0)))
        + w["w_latency"] * _norm(dec(metrics.get("latency_penalty_cash", 0)))
        + w["w_capacity"] * _norm(dec(metrics.get("capacity_crowding_penalty_cash", 0)))
        + w["w_fdr"] * _norm(dec(metrics.get("fdr_penalty_cash", 0)))
        + w["w_calibration"] * dec(metrics.get("calibration_gap", 0))
    )
    return positive - negative


def scored_rank_score(metrics: Mapping[str, Decimal | str | int]) -> str:
    return score(simulation_rank_score(metrics))

