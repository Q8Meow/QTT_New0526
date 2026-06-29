"""Scenario ladder computations."""

from __future__ import annotations

from decimal import Decimal

from .models import score

SCENARIO_FAMILIES = (
    "base_case",
    "fee_worse_case",
    "spread_wider_case",
    "slippage_worse_case",
    "latency_worse_case",
    "partial_fill_case",
    "depth_evaporation_case",
    "source_change_case",
    "event_lifecycle_transition_case",
    "market_status_change_case",
    "portfolio_exposure_stress_case",
    "combined_conservative_case",
)

SCENARIO_PENALTIES = {
    "base_case": Decimal("0.000"),
    "fee_worse_case": Decimal("0.015"),
    "spread_wider_case": Decimal("0.020"),
    "slippage_worse_case": Decimal("0.020"),
    "latency_worse_case": Decimal("0.018"),
    "partial_fill_case": Decimal("0.025"),
    "depth_evaporation_case": Decimal("0.035"),
    "source_change_case": Decimal("0.030"),
    "event_lifecycle_transition_case": Decimal("0.022"),
    "market_status_change_case": Decimal("0.025"),
    "portfolio_exposure_stress_case": Decimal("0.018"),
    "combined_conservative_case": Decimal("0.060"),
}


def scenario_result(base_net_pnl_cash: Decimal, lcb_cash: Decimal, scenario_family: str) -> dict[str, object]:
    penalty = SCENARIO_PENALTIES.get(scenario_family, Decimal("0.025"))
    expected = base_net_pnl_cash - penalty
    lcb = lcb_cash - penalty
    margin = expected
    return {
        "scenario_family": scenario_family,
        "scenario_expected_pnl_cash": score(expected),
        "scenario_lcb_pnl_cash": score(lcb),
        "scenario_no_trade_margin_cash": score(margin),
        "scenario_pass_flag": margin > Decimal("0"),
        "scenario_failure_reason": "" if margin > Decimal("0") else "NO_TRADE_OR_STRESS_DOMINATES_THIS_SCENARIO",
    }


def robustness_score(rows: list[dict[str, object]]) -> str:
    if not rows:
        return score(0)
    passed = sum(1 for row in rows if row.get("scenario_pass_flag") is True)
    return score(Decimal(passed) / Decimal(len(rows)))

