"""Algorithm registry and deterministic algorithm helpers for PR162B."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .calibration_formulas import probability_clipping
from .prediction_market_formulas import expected_value_binary, no_trade_decision, probability_edge
from .quantum_formulations import assemble_ising_input, assemble_qubo_input, exact_qubo_smoke_solve
from .risk_position_sizing_formulas import capped_position_size, kelly_fraction_binary, risk_budget_capped_position_size
from .technical_feature_formulas import midpoint, spread, z_score


def binary_edge_signal_algorithm(model_probability: float, market_probability: float, threshold: float) -> dict[str, Any]:
    edge = probability_edge(model_probability, market_probability)
    return {"edge": edge, "decision": no_trade_decision(edge, threshold)}


def expected_value_gate_algorithm(p_win: float, profit_if_win: float, loss_if_lose: float, threshold: float) -> dict[str, Any]:
    ev = expected_value_binary(p_win, profit_if_win, loss_if_lose)
    return {"expected_value": ev, "passes_gate": ev > float(threshold)}


def no_trade_zone_algorithm(edge: float, threshold: float) -> str:
    return no_trade_decision(edge, threshold)


def capped_kelly_position_size_algorithm(p_win: float, net_odds: float, fraction: float, cap: float) -> float:
    return capped_position_size(kelly_fraction_binary(p_win, net_odds) * float(fraction), cap)


def risk_budget_cap_algorithm(raw_size: float, risk_budget: float, unit_risk: float) -> float:
    return risk_budget_capped_position_size(raw_size, risk_budget, unit_risk)


def probability_clipping_algorithm(probability: float, epsilon: float) -> float:
    return probability_clipping(probability, epsilon)


def midpoint_spread_feature_algorithm(ask: float, bid: float) -> dict[str, float]:
    return {"midpoint": midpoint(ask, bid), "spread": spread(ask, bid)}


def z_score_signal_algorithm(value: float, mean: float, std: float, threshold: float) -> dict[str, Any]:
    score = z_score(value, mean, std)
    if abs(score) <= abs(float(threshold)):
        signal = "NO_SIGNAL"
    else:
        signal = "HIGH" if score > 0 else "LOW"
    return {"z_score": score, "signal": signal}


def strict_formula_binding_algorithm(qku_type: str, formula_family: str, market_scope_match_flag: bool) -> str:
    if not market_scope_match_flag:
        return "BLOCKED_NO_MARKET_SCOPE_MATCH"
    if qku_type in {"FORMULA_QKU", "RISK_QKU", "CONSTRAINT_QKU", "ATOMICROW_QKU", "OPTIMIZER_SETTING_QKU"}:
        return "STRICT_BINDING_CONFIRMED"
    if formula_family in {"quantum_hybrid", "classical_optimizer"} and qku_type in {"ALGORITHM_QKU", "PARAMETER_QKU"}:
        return "CANDIDATE_BINDING_REPLAY_PAPER_REQUIRED"
    return "BLOCKED_FORMULA_NOT_APPLICABLE"


def qubo_input_assembly_algorithm(Q: list[list[float]]) -> dict[str, Any]:
    return assemble_qubo_input(Q)


def ising_input_assembly_algorithm(h: list[float], J: list[tuple[int, int, float]]) -> dict[str, Any]:
    return assemble_ising_input(h, J)


def market_scope_activation_algorithm(primary_market_scope: str, has_input_binding: bool, confidence: str) -> str:
    if primary_market_scope not in c.STAGE1_ALLOWED_MARKET_SCOPES:
        return "DORMANT_NON_STAGE1_MARKET_SPECIFIC"
    if confidence in {"LOW_NAME_HEURISTIC_ONLY", "UNKNOWN_REQUIRES_OWNER_REVIEW"}:
        return "DORMANT_OWNER_REVIEW_REQUIRED"
    if not has_input_binding:
        return "DORMANT_MISSING_INPUT_BINDING"
    return "ACTIVE_STAGE1_REPLAY_PAPER_ONLY"


def dormant_qku_exclusion_algorithm(activation_status: str) -> bool:
    return not str(activation_status).startswith("DORMANT_")


def _function_path(function: str) -> tuple[str, str]:
    return (
        "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.algorithm_registry",
        function,
    )


def _spec(
    key: str,
    family: str,
    name: str,
    purpose: str,
    function: str,
    inputs: list[str],
    outputs: list[str],
    test_inputs: dict[str, Any],
    expected_output: Any,
    *,
    formula_refs: list[str] | None = None,
    solver_mapping_refs: list[str] | None = None,
) -> dict[str, Any]:
    module, func = _function_path(function)
    algorithm_id = f"PR162B-ALGORITHM-{key.upper()}"
    return {
        "algorithm_id": algorithm_id,
        "algorithm_family": family,
        "algorithm_name": name,
        "purpose": purpose,
        "pseudocode": [
            "validate inputs",
            "compute deterministic local candidate output",
            "return candidate output without live, private, order, optimizer, or backend execution",
        ],
        "implementation_module": module,
        "implementation_function": func,
        "input_fields": inputs,
        "output_fields": outputs,
        "parameter_refs": [],
        "formula_refs": formula_refs or [],
        "objective_refs": [],
        "constraint_refs": [],
        "solver_mapping_refs": solver_mapping_refs or [],
        "test_vector_refs": [f"PR162B-TEST-ALGORITHM-{key.upper()}-001"],
        "qku_refs": [],
        "market_scope": list(c.STAGE1_ALLOWED_MARKET_SCOPES),
        "stage1_activation_status": "ACTIVE_STAGE1_REPLAY_PAPER_ONLY",
        "smoke_execution_status": "ALGORITHM_TEST_VECTOR_EXECUTED",
        "replay_paper_required_flag": True,
        "live_use_allowed_flag": False,
        "created_by_pr": c.PR_ID,
        "test_vector": {
            "test_vector_id": f"PR162B-TEST-ALGORITHM-{key.upper()}-001",
            "formula_id_or_algorithm_id": algorithm_id,
            "implementation_function": func,
            "implementation_module": module,
            "inputs": test_inputs,
            "expected_output": expected_output,
            "tolerance": 1e-9,
            "unit": "unitless",
            "edge_case_flag": False,
            "invalid_input_flag": False,
            "source_reference": "PR162B_LOCAL_DETERMINISTIC_ALGORITHM_CONTRACT",
            "test_status": "ALGORITHM_TEST_VECTOR_EXECUTED",
            "qku_refs": [],
        },
    }


def algorithm_specs() -> list[dict[str, Any]]:
    return [
        _spec("binary_edge_signal_algorithm", "signal", "binary_edge_signal_algorithm", "Compute edge and no-trade/buy side candidate.", "binary_edge_signal_algorithm", ["model_probability", "market_probability", "threshold"], ["edge", "decision"], {"model_probability": 0.55, "market_probability": 0.5, "threshold": 0.02}, {"edge": 0.05, "decision": "BUY_YES"}),
        _spec("expected_value_gate_algorithm", "expected_value_gate", "expected_value_gate_algorithm", "Compute expected value and compare with threshold.", "expected_value_gate_algorithm", ["p_win", "profit_if_win", "loss_if_lose", "threshold"], ["expected_value", "passes_gate"], {"p_win": 0.55, "profit_if_win": 1.0, "loss_if_lose": 1.0, "threshold": 0.05}, {"expected_value": 0.1, "passes_gate": True}),
        _spec("no_trade_zone_algorithm", "expected_value_gate", "no_trade_zone_algorithm", "Map edge to no-trade or buy-side candidate.", "no_trade_zone_algorithm", ["edge", "threshold"], ["decision"], {"edge": 0.01, "threshold": 0.02}, "NO_TRADE"),
        _spec("capped_kelly_position_size_algorithm", "position_sizing", "capped_kelly_position_size_algorithm", "Compute fractional capped Kelly position size candidate.", "capped_kelly_position_size_algorithm", ["p_win", "net_odds", "fraction", "cap"], ["position_size"], {"p_win": 0.55, "net_odds": 1.0, "fraction": 0.5, "cap": 0.2}, 0.05),
        _spec("risk_budget_cap_algorithm", "risk_control", "risk_budget_cap_algorithm", "Apply risk-budget cap to raw size.", "risk_budget_cap_algorithm", ["raw_size", "risk_budget", "unit_risk"], ["position_size"], {"raw_size": 10, "risk_budget": 3, "unit_risk": 0.5}, 6.0),
        _spec("probability_clipping_algorithm", "feature_compute", "probability_clipping_algorithm", "Clip probability candidate to safe numeric domain.", "probability_clipping_algorithm", ["probability", "epsilon"], ["clipped_probability"], {"probability": 0.0, "epsilon": 0.01}, 0.01),
        _spec("midpoint_spread_feature_algorithm", "feature_compute", "midpoint_spread_feature_algorithm", "Compute bid-ask midpoint and spread.", "midpoint_spread_feature_algorithm", ["ask", "bid"], ["midpoint", "spread"], {"ask": 0.6, "bid": 0.4}, {"midpoint": 0.5, "spread": 0.2}),
        _spec("z_score_signal_algorithm", "feature_compute", "z_score_signal_algorithm", "Compute z-score and thresholded signal.", "z_score_signal_algorithm", ["value", "mean", "std", "threshold"], ["z_score", "signal"], {"value": 12, "mean": 10, "std": 2, "threshold": 0.5}, {"z_score": 1.0, "signal": "HIGH"}),
        _spec("strict_formula_binding_algorithm", "binding_governance", "strict_formula_binding_algorithm", "Require qku family and market-scope proof before binding.", "strict_formula_binding_algorithm", ["qku_type", "formula_family", "market_scope_match_flag"], ["binding_status"], {"qku_type": "FORMULA_QKU", "formula_family": "prediction_market", "market_scope_match_flag": True}, "STRICT_BINDING_CONFIRMED"),
        _spec("exact_qubo_smoke_enumeration_algorithm", "solver_input_assembly", "exact_qubo_smoke_enumeration_algorithm", "Enumerate tiny local QUBO inputs with no trading or backend evidence.", "exact_qubo_smoke_solve", ["Q", "max_variables"], ["best_x", "best_energy"], {"Q": [[2.0, 3.0], [0.0, 4.0]], "max_variables": 12}, {"best_x": [0, 0], "best_energy": 0.0, "status": "SMOKE_EXECUTED_NO_TRADING_EVIDENCE", "variable_count": 2}),
        _spec("qubo_input_assembly_algorithm", "solver_input_assembly", "qubo_input_assembly_algorithm", "Assemble QUBO solver-input metadata without solve.", "qubo_input_assembly_algorithm", ["Q"], ["solver_input"], {"Q": [[1.0, 0.0], [0.0, 2.0]]}, {"input_representation": "QUBO_MATRIX", "variable_type": "BINARY", "variable_count": 2, "Q": [[1.0, 0.0], [0.0, 2.0]], "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE"}),
        _spec("ising_input_assembly_algorithm", "solver_input_assembly", "ising_input_assembly_algorithm", "Assemble Ising solver-input metadata without solve.", "ising_input_assembly_algorithm", ["h", "J"], ["solver_input"], {"h": [1.0, -0.5], "J": [(0, 1, 0.25)]}, {"input_representation": "ISING_H_J", "variable_type": "SPIN", "variable_count": 2, "h": [1.0, -0.5], "J": {"0,1": 0.25}, "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE"}),
        _spec("market_scope_activation_algorithm", "market_scope_governance", "market_scope_activation_algorithm", "Decide active/dormant status from strict market-scope inputs.", "market_scope_activation_algorithm", ["primary_market_scope", "has_input_binding", "confidence"], ["activation_status"], {"primary_market_scope": "PREDICTION_MARKET_BINARY_EVENT_CONTRACT", "has_input_binding": True, "confidence": "HIGH_EXPLICIT_QKU_FAMILY"}, "ACTIVE_STAGE1_REPLAY_PAPER_ONLY"),
        _spec("dormant_qku_exclusion_algorithm", "market_scope_governance", "dormant_qku_exclusion_algorithm", "Exclude dormant QKUs from execution-router allowlists.", "dormant_qku_exclusion_algorithm", ["activation_status"], ["allowed_flag"], {"activation_status": "DORMANT_NON_STAGE1_MARKET_SPECIFIC"}, False),
    ]


def algorithm_records() -> list[dict[str, Any]]:
    return [{key: value for key, value in spec.items() if key != "test_vector"} for spec in algorithm_specs()]


def algorithm_test_vector_records() -> list[dict[str, Any]]:
    return [dict(spec["test_vector"]) for spec in algorithm_specs()]
