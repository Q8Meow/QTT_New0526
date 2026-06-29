"""Execution-adjusted score helpers for PR168-RANK4."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import dec
from .policy import policy_value


COMPONENT_WEIGHTS = {
    "net": "score_weight_net_expected_pnl_default",
    "lcb": "score_weight_lcb_default",
    "notrade": "score_weight_no_trade_margin_default",
    "fill": "score_weight_fill_probability_default",
    "latency": "score_weight_latency_quality_default",
    "capacity": "score_weight_capacity_quality_default",
    "portfolio": "score_weight_portfolio_marginal_utility_default",
    "scenario": "score_weight_scenario_robustness_default",
    "calib": "score_weight_calibration_quality_default",
    "prov": "score_weight_data_provenance_quality_default",
    "route": "score_weight_agent_no_orphan_quality_default",
    "qstruct": "score_weight_quantum_structural_handoff_default",
    "paper": "score_weight_paper_readiness_default",
}


def weighted_score(normalized: dict[str, Any], penalties: dict[str, Any]) -> Decimal:
    total = Decimal("0")
    for component, policy_name in COMPONENT_WEIGHTS.items():
        total += policy_value(policy_name) * dec(normalized.get(component))
    for value in penalties.values():
        total -= dec(value)
    return total

