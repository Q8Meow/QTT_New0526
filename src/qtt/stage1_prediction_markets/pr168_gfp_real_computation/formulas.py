"""Convenience exports for PR168-GFP formula functions."""

from __future__ import annotations

from .decision import lower_confidence_bound_edge, no_trade_decision_reason, positive_negative_decision
from .execution_costs import (
    adverse_selection_penalty,
    capacity_crowding_penalty,
    execution_adjusted_edge,
    explicit_fee_cost,
    implementation_shortfall,
    latency_decay,
    market_impact_penalty,
    partial_fill_penalty,
    queue_nonfill_penalty,
    slippage_cost,
    spread_cost,
)
from .fill_queue_latency import partial_fill, queue_fill_probability
from .overfit_controls import (
    deflated_score_proxy,
    false_discovery_penalty,
    lcb_from_mean_se,
    overfit_fdr_penalty,
    shrinkage_probability,
)
from .pnl import net_expected_pnl_candidate
from .portfolio_utility import expected_shortfall_candidate, marginal_utility, risk_budget_check
from .prediction_market_math import (
    binary_contract_expected_value,
    expected_value,
    expected_value_from_edge,
    gross_edge,
    market_implied_probability,
)
from .quantum_objectives import (
    build_bqm_objective,
    build_cqm_objective,
    build_dqm_objective,
    build_ising_objective,
    build_quadprogram_objective,
    build_qubo_objective,
    compute_classical_fallback_solution,
)
from .tca import tca_decomposition


__all__ = [
    "adverse_selection_penalty",
    "binary_contract_expected_value",
    "build_bqm_objective",
    "build_cqm_objective",
    "build_dqm_objective",
    "build_ising_objective",
    "build_quadprogram_objective",
    "build_qubo_objective",
    "capacity_crowding_penalty",
    "compute_classical_fallback_solution",
    "deflated_score_proxy",
    "execution_adjusted_edge",
    "expected_shortfall_candidate",
    "expected_value",
    "expected_value_from_edge",
    "explicit_fee_cost",
    "false_discovery_penalty",
    "gross_edge",
    "implementation_shortfall",
    "latency_decay",
    "lcb_from_mean_se",
    "lower_confidence_bound_edge",
    "market_impact_penalty",
    "market_implied_probability",
    "marginal_utility",
    "net_expected_pnl_candidate",
    "no_trade_decision_reason",
    "overfit_fdr_penalty",
    "partial_fill",
    "partial_fill_penalty",
    "positive_negative_decision",
    "queue_fill_probability",
    "queue_nonfill_penalty",
    "risk_budget_check",
    "shrinkage_probability",
    "slippage_cost",
    "spread_cost",
    "tca_decomposition",
]
