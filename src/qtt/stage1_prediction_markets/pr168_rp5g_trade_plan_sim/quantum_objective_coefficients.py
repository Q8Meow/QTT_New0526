"""Quantum objective coefficient helpers."""

from __future__ import annotations

from decimal import Decimal

from .models import score


def economic_objective_terms(net: Decimal, lcb: Decimal, tca: Decimal, fdr: Decimal, capacity: Decimal, portfolio: Decimal) -> dict[str, str]:
    return {
        "net_expected_pnl_term": score(net),
        "LCB_term": score(lcb),
        "TCA_penalty_term": score(-tca),
        "overfit_fdr_penalty_term": score(-fdr),
        "capacity_crowding_penalty_term": score(-capacity),
        "portfolio_marginal_utility_term": score(portfolio),
        "no_trade_selection_term": score(0),
    }

