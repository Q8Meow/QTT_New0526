"""Pareto frontier and dominance helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import dec


PARETO_DIMS = (
    ("net_expected_pnl_cash", True),
    ("lower_confidence_bound_pnl_cash", True),
    ("candidate_minus_no_trade_cash", True),
    ("fill_probability", True),
    ("portfolio_marginal_utility_cash", True),
    ("scenario_robustness_score", True),
    ("TCA_total_cash", False),
    ("latency_decay_penalty_cash", False),
    ("capacity_penalty_cash", False),
    ("crowding_penalty_cash", False),
    ("fdr_penalty_cash", False),
    ("calibration_gap", False),
)


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    better_or_equal = True
    strictly_better = False
    for key, higher in PARETO_DIMS:
        a = dec(left.get(key))
        b = dec(right.get(key))
        if higher:
            better_or_equal = better_or_equal and a >= b
            strictly_better = strictly_better or a > b
        else:
            better_or_equal = better_or_equal and a <= b
            strictly_better = strictly_better or a < b
    return better_or_equal and strictly_better


def rank_tuple(row: dict[str, Any]) -> tuple[Decimal, str]:
    return (dec(row.get("rank4_execution_adjusted_score")), str(row.get("candidate_id")))

