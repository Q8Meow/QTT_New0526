from __future__ import annotations

"""Compact table-driven fixtures used by both runtime tests and the validator.

The validator derives expectations from execution; these fixtures contain
inputs and applicability contexts only, never expected final results.
"""

from copy import deepcopy
from typing import Any


_DIFFERENCE_CARDS = {"A25", "B16", "D12", "D20", "F24", "F25", "F44", "F45"}
_RATIO_CARDS = {"B11", "D10", "F39", "F40", "G09"}


def _j_fixture(card_id: str) -> dict[str, Any]:
    if card_id == "J01":
        return {"support": [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], "utilities": [0.0, 1.0, 0.5], "weights": [0.2, 0.5, 0.3], "transport_cost_matrix": [[0.0, 1.0, 1.0], [1.0, 0.0, 1.4], [1.0, 1.4, 0.0]], "ambiguity_radius": 0.2, "transport_metric": "DECLARED_FINITE_COST_MATRIX", "sensitivity_radii": [0.0, 0.1, 0.2], "no_trade_utility": 0.0}
    if card_id == "J02":
        return {"constraint_id": "fill_ttl", "constraint_residuals": [-1.0, -0.5, 0.2, -0.1], "target_violation_probability": 0.6, "confidence_level": 0.8, "confidence_method": "EXACT_BINOMIAL_IID", "threshold_provenance": "FIXTURE_POLICY"}
    if card_id == "J03":
        return {"reference_samples": [[0.0], [0.1], [0.2], [0.3]], "current_samples": [[1.0], [1.1], [1.2], [1.3]], "bandwidth": 0.5, "permutations": 31, "seed": 7, "alpha": 0.1, "resampling_method": "IID_PERMUTATION", "trial_family_id": "FIXTURE_SHIFT_FAMILY"}
    if card_id == "J04":
        return {"kernel": [[2.0, 0.2], [0.2, 1.0]], "jitter": 1e-9, "jitter_provenance": "NUMERICAL_FIXTURE", "tolerance": 1e-12, "raw_economic_utility_ref": "FIXTURE_UTILITY", "opportunity_cost_ref": "FIXTURE_OPPORTUNITY"}
    if card_id == "J05":
        return {"outcomes": [0.0, 1.0, 1.0, 0.0], "log_target_density": [0.0, 0.0, 0.0, 0.0], "log_proposal_density": [0.0, 0.0, 0.0, 0.0], "target_samples": [0.0, 1.0, 1.0, 0.0], "seed": 11}
    if card_id == "J06":
        return {"objective_sense": "MINIMIZE", "objective_coefficients": [1.0, 2.0], "constraint_matrix": [[1.0, 1.0]], "constraint_senses": [">="], "constraint_rhs": [1.0], "primal_solution": [1.0, 0.0], "dual_solution": [1.0], "dual_bound": 1.0, "input_lock_ref": "LOCK-1", "dual_input_lock_ref": "LOCK-1", "formulation_ref": "FORM-1", "dual_formulation_ref": "FORM-1", "tolerance": 1e-9}
    if card_id == "J07":
        return {"linear": [-2.02, 1.01], "quadratic": {"0,1": 0.19}, "offset": 0.0, "prune_threshold": 0.01, "quantization_step": 0.1, "candidate_assignments": {"champion": [1, 0], "runner_up": [0, 0], "no_trade": [0, 0]}, "penalty_terms": [], "feasibility_constraints": [], "inverse_economic_map": {"scale": 1.0, "offset": 0.0}, "exhaustive_variable_limit": 16}
    objective = {"00": 0.0, "01": 1.0, "10": 1.0, "11": 2.0}
    return {"variable_count": 2, "generators": [[1, 0]], "objective_values": objective, "feasible_values": {key: True for key in objective}, "objective_sense": "MINIMIZE", "source_formulation_ref": "FORM-ORIGINAL", "reduced_formulation_ref": "FORM-REDUCED"}


def valid_fixture(card_id: str) -> dict[str, Any]:
    if card_id.startswith("J"):
        return _j_fixture(card_id)
    values: dict[str, Any] = {"values": [0.1, 0.2, 0.3], "__problem_size__": 3}
    overrides: dict[str, dict[str, Any]] = {
        "A01": {"realized_net_cash": ["1.10", "-0.20", "0.40"]},
        "A02": {"exit_or_settlement_cash": 10, "entry_cash": 7, "unique_costs": [1], "unique_rebates": [0.5]},
        "A03": {"probabilities": [0.25, 0.75], "branch_net_cash": [-1, 2]},
        "A06": {"net_cash_lcb": 2, "expected_holding_seconds": 4},
        "A07": {"net_cash_lcb": 2, "capital_at_risk": 5, "expected_holding_seconds": 4},
        "A08": {"owner_minimum_cash_profit": 1, "round_trip_cost_uncertainty_hurdle": 2, "capital_opportunity_cost_hurdle": 1.5, "risk_reserve_hurdle": 1.25, "minimum_profit_bps": 10, "deployed_capital": 1000},
        "A09": {"quantity": 3, "levels": [{"price": 0.6, "quantity": 2}, {"price": 0.5, "quantity": 2}]},
        "A10": {"quantity": 3, "levels": [{"price": 0.4, "quantity": 2}, {"price": 0.5, "quantity": 2}]},
        "B09": {"hazard_increments": [0.1, 0.2]},
        "B11": {"bid_size": 60, "ask_size": 40},
        "B12": {"best_bid": 0.4, "best_ask": 0.5, "bid_size": 60, "ask_size": 40},
        "C01": {"probabilities": [0.2, 0.8], "outcomes": [0, 1]},
        "C02": {"probabilities": [0.2, 0.8], "outcomes": [0, 1]},
        "C05": {"weights": [1, 2, 1]},
        "C10": {"p_values": [0.01, 0.2, 0.03], "q": 0.1},
        "C11": {"p_values": [0.01, 0.2, 0.03], "q": 0.1},
        "D01": {"losses": [1, 2, 5], "alpha": 0.8, "weights": [0.2, 0.3, 0.5]},
        "D05": {"shares": [0.5, 0.3, 0.2]},
        "D06": {"shares": [0.5, 0.3, 0.2]},
        "D09": {"equity": [10, 12, 9, 11]},
        "D10": {"capital_used": 2, "capital_budget": 5},
        "E03": {"probabilities": [0.4, 0.6]},
        "E04": {"probabilities": [0.4, 0.6]},
        "E05": {"probability_subset": 0.3, "probability_superset": 0.6},
        "E06": {"probability_intersection": 0.2, "probability_a": 0.4, "probability_b": 0.5},
        "E07": {"probability_subset": 0.3, "probability_superset": 0.6},
        "E08": {"probability_subset": 0.3, "probability_superset": 0.6},
        "F08": {"lambda_onehot": 2.0, "selections": [1.0, 0.0, 0.0]},
        "F20": {"probabilities": [0.2, 0.3, 0.5]},
        "F23": {"left": ["a", "b"], "right": ["b", "c"]},
        "F39": {"numerator": 3, "denominator": 4},
        "F40": {"numerator": 1, "denominator": 4},
        "G09": {"numerator": 3, "denominator": 4},
        "G10": {"p_success": 0.5, "p_target": 0.95, "run_seconds": 2},
        "H05": {"losses": [1, 2, 5], "alpha": 0.8, "weights": [0.2, 0.3, 0.5]},
        "H14": {"exit_or_settlement_cash": 10, "entry_cash": 7, "unique_costs": [1], "unique_rebates": [0.5], "branch_net_cash": 2.5},
        "I04": {"requirements": [{"name": "x", "required": True, "critical": True, "resolved_valid": True}]},
        "I07": {"reference_time": 10, "windows": [{"valid_until": 20, "ttl": 20}]},
        "I08": {"components": {"feature_snapshot_ms": 1, "formula_compute_ms": 2}},
        "I09": {"total_decision_latency_ms": 3, "latency_budget_ms": 10, "min_material_valid_until_ms": 30, "input_lock_time_ms": 10},
        "I10": {"severity_desc": 1, "economic_ttl_asc": 2, "hard_dependency_block_count_desc": 0, "downstream_blocked_value_desc": 3, "value_of_information_per_compute_desc": 4, "queue_age_desc": 5, "deterministic_tie_break_key_asc": "A"},
    }
    if card_id in _DIFFERENCE_CARDS:
        return {"left": 2.0, "right": 1.0, "__problem_size__": 2}
    if card_id == "F23":
        return overrides[card_id]
    if card_id == "D29":
        return {"left": [2.0, 1.0], "right": [1.0, 2.0], "senses": ["MAXIMIZE", "MINIMIZE"]}
    return deepcopy(overrides.get(card_id, values))


def missing_fixture(card_id: str) -> dict[str, Any]:
    del card_id
    return {}


def boundary_fixture(card_id: str) -> dict[str, Any]:
    fixture = valid_fixture(card_id)
    fixture["__problem_size__"] = 65
    return fixture


def applicability_context(card_id: str, *, positive: bool) -> dict[str, Any]:
    return {"card_ids": [card_id] if positive else [], "stage": "PRETRADE" if not card_id.startswith(("F", "J")) else "QBENCH", "mode": "OFFLINE", "market": "prediction_market"}
