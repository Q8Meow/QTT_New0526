"""PR162C formula and algorithm delta records with test vectors."""

from __future__ import annotations

import importlib
import math
from typing import Any

from . import constants as c


SOURCE_LOCATORS = {
    "kalshi_docs": "https://docs.kalshi.com/",
    "kalshi_candlesticks": "https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks",
    "polymarket_docs": "https://docs.polymarket.com/api-reference",
    "forecastex_data": "https://www.forecastex.com/data/",
    "sklearn_metrics": "https://scikit-learn.org/stable/modules/model_evaluation.html",
    "numpy_stats": "https://numpy.org/doc/stable/reference/routines.statistics.html",
    "dwave_models": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
    "qiskit_optimization": "https://qiskit-community.github.io/qiskit-optimization/",
    "owner_pr162c": "OWNER_PR162C_INTERNAL_APPROVED_CANDIDATE",
}


def _function_path(module: str, function: str) -> tuple[str, str]:
    return f"{c.PACKAGE_IMPORT}.{module}", function


def _formula_spec(
    key: str,
    family: str,
    name: str,
    expression: str,
    definition: str,
    module: str,
    function: str,
    inputs: list[str],
    output: str,
    source_class: str,
    source_locator: str,
    source_title: str,
    market_scope: str,
    test_inputs: dict[str, Any],
    expected_output: Any,
    *,
    tolerance: float = 1e-9,
    units: str = "unitless",
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    implementation_module, implementation_function = _function_path(module, function)
    formula_id = f"PR162C-FORMULA-DELTA-{key.upper()}"
    test_vector_id = f"PR162C-TEST-FORMULA-DELTA-{key.upper()}-001"
    return {
        "formula_id": formula_id,
        "formula_family": family,
        "formula_name": name,
        "mathematical_expression": expression,
        "mathematical_expression_latex": expression,
        "plain_english_definition": definition,
        "variables": variables or {field: field for field in inputs},
        "units": units,
        "input_fields": inputs,
        "output_fields": [output],
        "valid_input_domain": "bounded numeric inputs documented by implementation validation",
        "invalid_input_conditions": [
            "missing input",
            "non-numeric input where numeric input is required",
            "domain violations raise ValueError",
        ],
        "missing_value_policy": "reject missing values before formula execution",
        "normalization_policy": "caller supplies normalized numeric values",
        "source_class": source_class,
        "source_locator": source_locator,
        "source_title": source_title,
        "retrieval_timestamp": None,
        "authority_class": c.AUTHORITY_CLASS,
        "official_truth_flag": source_class.startswith("OFFICIAL_"),
        "candidate_provisional_flag": True,
        "derivation_method": "PR162C_LOCAL_DETERMINISTIC_FORMULA_DELTA",
        "formula_value_field_dependencies": inputs,
        "dataset_requirement_refs": [],
        "replay_paper_candidate_route": "PR162R_ADAPTER_RERUN_AFTER_STRICT_DATASETS",
        "qtt_agent_consumer_route": _agents_for_family(family),
        "test_vector_refs": [test_vector_id],
        "not_official_truth_if_non_official": not source_class.startswith("OFFICIAL_"),
        "not_live_authority": True,
        "implementation_status": "IMPLEMENTED_DETERMINISTIC_PYTHON",
        "implementation_module": implementation_module,
        "implementation_function": implementation_function,
        "qku_id_refs": [],
        "formula_refs": [],
        "objective_refs": [],
        "constraint_refs": [],
        "parameter_refs": [],
        "solver_refs": [],
        "created_by_pr": c.PR_ID,
        "test_vector": {
            "test_vector_id": test_vector_id,
            "formula_id": formula_id,
            "inputs": test_inputs,
            "expected_output": expected_output,
            "tolerance": tolerance,
            "unit": units,
            "edge_case_tests": [],
            "invalid_input_tests": ["domain violations raise ValueError"],
            "source_reference": source_locator,
            "implementation_function_ref": f"{implementation_module}.{implementation_function}",
            "implementation_module": implementation_module,
            "implementation_function": implementation_function,
            "created_by_pr": c.PR_ID,
        },
    }


def formula_delta_specs() -> list[dict[str, Any]]:
    pm = "PREDICTION_MARKET_BINARY_EVENT_CONTRACT"
    math_scope = "MARKET_AGNOSTIC_MATH"
    risk = "MARKET_AGNOSTIC_RISK"
    feature = "MARKET_AGNOSTIC_FEATURE"
    opt = "MARKET_AGNOSTIC_OPTIMIZER"
    return [
        _formula_spec("yes_contract_ev", "prediction_market", "yes_contract_ev", "EV_yes = p_model*payout - ask_yes", "Expected value candidate for buying a yes contract at adjusted ask.", "prediction_market_formulas", "yes_contract_ev", ["p_model", "ask_price_yes_adjusted", "payout"], "yes_ev", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["kalshi_docs"], "Kalshi public documentation locator", pm, {"p_model": 0.55, "ask_price_yes_adjusted": 0.50, "payout": 1.0}, 0.05),
        _formula_spec("no_contract_ev", "prediction_market", "no_contract_ev", "EV_no = (1-p_model)*payout - ask_no", "Expected value candidate for buying a no contract at adjusted ask.", "prediction_market_formulas", "no_contract_ev", ["p_model", "ask_price_no_adjusted", "payout"], "no_ev", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket_docs"], "Polymarket API documentation locator", pm, {"p_model": 0.55, "ask_price_no_adjusted": 0.40, "payout": 1.0}, 0.04999999999999993),
        _formula_spec("expected_net_profit", "prediction_market", "expected_net_profit", "net = EV - fees - slippage - latency_penalty", "Candidate net expected profit after explicit cost adjustments.", "prediction_market_formulas", "expected_net_profit", ["expected_value", "fees", "slippage", "latency_penalty"], "expected_net_profit", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["owner_pr162c"], "Owner-approved PR162C internal cost adjustment candidate", pm, {"expected_value": 0.10, "fees": 0.01, "slippage": 0.02, "latency_penalty": 0.03}, 0.04),
        _formula_spec("edge_yes", "prediction_market", "edge_yes", "edge_yes = p_model - ask_yes_adjusted", "Candidate probability edge for yes side.", "prediction_market_formulas", "edge_yes", ["p_model", "ask_price_yes_adjusted"], "edge_yes", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket_docs"], "Polymarket public API documentation locator", pm, {"p_model": 0.60, "ask_price_yes_adjusted": 0.55}, 0.04999999999999993),
        _formula_spec("edge_no", "prediction_market", "edge_no", "edge_no = (1-p_model) - ask_no_adjusted", "Candidate probability edge for no side.", "prediction_market_formulas", "edge_no", ["p_model", "ask_price_no_adjusted"], "edge_no", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket_docs"], "Polymarket public API documentation locator", pm, {"p_model": 0.60, "ask_price_no_adjusted": 0.35}, 0.050000000000000044),
        _formula_spec("matched_yes_no_bundle_cost", "prediction_market", "matched_yes_no_bundle_cost", "cost = yes_ask + no_ask", "Candidate matched yes/no bundle cost.", "prediction_market_formulas", "matched_yes_no_bundle_cost", ["yes_ask", "no_ask"], "bundle_cost", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["kalshi_docs"], "Kalshi public documentation locator", pm, {"yes_ask": 0.48, "no_ask": 0.49}, 0.97),
        _formula_spec("bounded_arbitrage_candidate_edge", "prediction_market", "bounded_arbitrage_candidate_edge", "edge = 1 - yes_ask - no_ask - fee_buffer", "Candidate bounded dislocation edge before replay/paper validation.", "prediction_market_formulas", "bounded_arbitrage_candidate_edge", ["yes_ask", "no_ask", "fee_buffer"], "arbitrage_candidate_edge", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["kalshi_docs"], "Kalshi public documentation locator", pm, {"yes_ask": 0.48, "no_ask": 0.49, "fee_buffer": 0.01}, 0.020000000000000018),
        _formula_spec("same_event_price_dislocation", "prediction_market", "same_event_price_dislocation", "abs(price_a - price_b)", "Candidate same-event price dislocation.", "prediction_market_formulas", "same_event_price_dislocation", ["price_a", "price_b"], "price_dislocation", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["forecastex_data"], "ForecastEx public data locator", pm, {"price_a": 0.52, "price_b": 0.47}, 0.050000000000000044),
        _formula_spec("liquidity_feasible_dislocation", "prediction_market", "liquidity_feasible_dislocation", "dislocation > 0 and observed_volume >= min_volume", "Boolean candidate for dislocation with minimum volume support.", "prediction_market_formulas", "liquidity_feasible_dislocation", ["dislocation", "min_volume", "observed_volume"], "liquidity_feasible", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["forecastex_data"], "ForecastEx public data locator", pm, {"dislocation": 0.05, "min_volume": 100, "observed_volume": 120}, True, units="boolean"),
        _formula_spec("forecast_sharpness_candidate", "calibration", "forecast_sharpness_candidate", "mean(abs(p_i - 0.5))", "Candidate measure of forecast sharpness.", "calibration_formulas", "forecast_sharpness_candidate", ["probabilities"], "forecast_sharpness", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn_metrics"], "scikit-learn model evaluation documentation locator", math_scope, {"probabilities": [0.2, 0.8, 0.5]}, 0.20000000000000004),
        _formula_spec("reliability_bin_calibration_candidate", "calibration", "reliability_bin_calibration_candidate", "abs(mean(p)-mean(y))", "Single-bin candidate calibration gap.", "calibration_formulas", "reliability_bin_calibration_candidate", ["predicted_probabilities", "observed_outcomes"], "calibration_gap", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn_metrics"], "scikit-learn model evaluation documentation locator", math_scope, {"predicted_probabilities": [0.8, 0.6], "observed_outcomes": [1, 0]}, 0.19999999999999996),
        _formula_spec("drawdown_capped_kelly", "risk_sizing", "drawdown_capped_kelly", "clip(f_kelly*(1-dd/max_dd), +/- cap)", "Candidate Kelly fraction reduced by drawdown pressure.", "risk_sizing_formulas", "drawdown_capped_kelly", ["kelly_fraction", "max_fraction", "drawdown", "max_drawdown"], "drawdown_capped_kelly", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["owner_pr162c"], "Owner-approved PR162C internal risk candidate", risk, {"kelly_fraction": 0.4, "max_fraction": 0.2, "drawdown": 0.1, "max_drawdown": 0.2}, 0.2),
        _formula_spec("liquidity_adjusted_size", "risk_sizing", "liquidity_adjusted_size", "clip(raw_size, +/- available_liquidity*cap)", "Candidate position size capped by liquidity.", "risk_sizing_formulas", "liquidity_adjusted_size", ["raw_size", "available_liquidity", "liquidity_fraction_cap"], "liquidity_adjusted_size", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["owner_pr162c"], "Owner-approved PR162C internal liquidity candidate", risk, {"raw_size": 50, "available_liquidity": 100, "liquidity_fraction_cap": 0.25}, 25.0),
        _formula_spec("max_position_by_budget", "risk_sizing", "max_position_by_budget", "budget / price", "Maximum position quantity by budget and price.", "risk_sizing_formulas", "max_position_by_budget", ["budget", "price"], "max_position", "OWNER_APPROVED_FORMULA_OR_VALUE_CANDIDATE", SOURCE_LOCATORS["owner_pr162c"], "Owner-approved PR162C internal sizing candidate", risk, {"budget": 100, "price": 0.5}, 200.0),
        _formula_spec("drawdown_penalized_score", "risk_sizing", "drawdown_penalized_score", "score - weight*drawdown", "Candidate drawdown-penalized score.", "risk_sizing_formulas", "drawdown_penalized_score", ["score", "drawdown", "penalty_weight"], "drawdown_penalized_score", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["owner_pr162c"], "Owner-approved PR162C internal score candidate", risk, {"score": 1.0, "drawdown": 0.2, "penalty_weight": 0.5}, 0.9),
        _formula_spec("correlation_penalized_portfolio_score", "portfolio_objectives", "correlation_penalized_portfolio_score", "return - weight*abs(correlation)", "Candidate portfolio score penalizing correlation.", "portfolio_objectives", "correlation_penalized_portfolio_score", ["expected_return", "average_pairwise_correlation", "penalty_weight"], "correlation_penalized_score", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy_stats"], "NumPy statistics documentation locator", opt, {"expected_return": 0.12, "average_pairwise_correlation": 0.5, "penalty_weight": 0.1}, 0.06999999999999999),
        _formula_spec("multi_objective_weighted_sum", "portfolio_objectives", "multi_objective_weighted_sum", "sum(w_i*x_i)", "Candidate multi-objective weighted sum.", "portfolio_objectives", "multi_objective_weighted_sum", ["values", "weights"], "weighted_sum", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy_stats"], "NumPy statistics documentation locator", opt, {"values": [1, 2, 3], "weights": [0.2, 0.3, 0.5]}, 2.3),
        _formula_spec("time_to_resolution_seconds", "technical_feature", "time_to_resolution", "max(0, resolution_ts - observation_ts)", "Time remaining until resolution candidate.", "technical_feature_formulas", "time_to_resolution_seconds", ["observation_ts", "resolution_ts"], "time_to_resolution_seconds", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["kalshi_candlesticks"], "Kalshi candlestick documentation locator", feature, {"observation_ts": 100.0, "resolution_ts": 160.0}, 60.0, units="seconds"),
        _formula_spec("price_momentum", "technical_feature", "price_momentum", "current_price - previous_price", "Candidate price momentum.", "technical_feature_formulas", "price_momentum", ["current_price", "previous_price"], "price_momentum", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket_docs"], "Polymarket public API documentation locator", feature, {"current_price": 0.55, "previous_price": 0.50}, 0.050000000000000044),
        _formula_spec("volume_momentum", "technical_feature", "volume_momentum", "current_volume - previous_volume", "Candidate volume momentum.", "technical_feature_formulas", "volume_momentum", ["current_volume", "previous_volume"], "volume_momentum", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["forecastex_data"], "ForecastEx public data locator", feature, {"current_volume": 120, "previous_volume": 100}, 20.0),
        _formula_spec("spread_change", "technical_feature", "spread_change", "current_spread - previous_spread", "Candidate spread change feature.", "technical_feature_formulas", "spread_change", ["current_spread", "previous_spread"], "spread_change", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["kalshi_candlesticks"], "Kalshi candlestick documentation locator", feature, {"current_spread": 0.06, "previous_spread": 0.04}, 0.019999999999999997),
        _formula_spec("orderbook_depth_proxy", "technical_feature", "orderbook_depth_proxy", "bid_size + ask_size", "Candidate order-book depth proxy.", "technical_feature_formulas", "orderbook_depth_proxy", ["bid_size", "ask_size"], "orderbook_depth_proxy", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket_docs"], "Polymarket public API documentation locator", feature, {"bid_size": 60, "ask_size": 40}, 100.0),
        _formula_spec("liquidity_score", "technical_feature", "liquidity_score", "volume / max(spread, epsilon)", "Candidate liquidity score.", "technical_feature_formulas", "liquidity_score", ["volume", "spread", "epsilon"], "liquidity_score", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["forecastex_data"], "ForecastEx public data locator", feature, {"volume": 100, "spread": 0.5, "epsilon": 1e-9}, 200.0),
        _formula_spec("qubo_to_ising_linear_terms", "quantum_hybrid", "QUBO-to-Ising mapping candidate", "Q -> h terms", "Local QUBO-to-Ising linear-term assembly candidate without solving.", "quantum_formulations", "qubo_to_ising_linear_terms", ["Q"], "ising_linear_terms", "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE", SOURCE_LOCATORS["qiskit_optimization"], "Qiskit Optimization documentation locator", opt, {"Q": [[2, 0], [0, 4]]}, {"h": [1.0, 2.0], "variable_count": 2, "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE"}),
        _formula_spec("constraint_penalty", "quantum_hybrid", "constraint_penalty", "lambda*(Ax-b)^2", "Penalty term for constraint violation.", "quantum_formulations", "constraint_penalty", ["Ax_minus_b", "penalty_lambda"], "constraint_penalty", "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE", SOURCE_LOCATORS["dwave_models"], "D-Wave model documentation locator", opt, {"Ax_minus_b": 2.0, "penalty_lambda": 3.0}, 12.0),
    ]


def formula_delta_records() -> list[dict[str, Any]]:
    return [{key: value for key, value in spec.items() if key != "test_vector"} for spec in formula_delta_specs()]


def formula_test_vector_delta_records() -> list[dict[str, Any]]:
    return [dict(spec["test_vector"]) for spec in formula_delta_specs()]


def algorithm_delta_records() -> list[dict[str, Any]]:
    return [
        {
            "algorithm_id": "PR162C-ALGORITHM-DELTA-STRICT_FIELD_COVERAGE_AUDIT",
            "algorithm_family": "dataset_strict_coverage",
            "algorithm_name": "strict_field_coverage_audit",
            "plain_english_definition": "Compares required PR162B input fields with PR162C repo-local candidate fields.",
            "source_class": "OWNER_APPROVED_FORMULA_OR_VALUE_CANDIDATE",
            "source_locator": SOURCE_LOCATORS["owner_pr162c"],
            "source_title": "Owner-approved PR162C strict coverage audit algorithm",
            "authority_class": c.AUTHORITY_CLASS,
            "candidate_provisional_flag": True,
            "official_truth_flag": False,
            "implementation_status": "IMPLEMENTED_DETERMINISTIC_PYTHON",
            "implementation_module": f"{c.PACKAGE_IMPORT}.qku_field_coverage",
            "implementation_function": "strict_field_coverage_status",
            "test_vector_refs": ["PR162C-TEST-ALGORITHM-DELTA-STRICT_FIELD_COVERAGE_AUDIT-001"],
            "not_official_truth_if_non_official": True,
            "not_live_authority": True,
            "qtt_agent_consumer_route": ["QTT_RESEARCH_AGENT", "QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"],
            "created_by_pr": c.PR_ID,
        },
        {
            "algorithm_id": "PR162C-ALGORITHM-DELTA-QUBO_INPUT_ASSEMBLY_AUDIT",
            "algorithm_family": "quantum_solver_input_assembly",
            "algorithm_name": "qubo_input_assembly_audit",
            "plain_english_definition": "Assembles QUBO input metadata without solving or backend execution.",
            "source_class": "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
            "source_locator": SOURCE_LOCATORS["dwave_models"],
            "source_title": "D-Wave model documentation locator",
            "authority_class": c.AUTHORITY_CLASS,
            "candidate_provisional_flag": True,
            "official_truth_flag": True,
            "implementation_status": "IMPLEMENTED_SOLVER_INPUT_ASSEMBLY_ONLY",
            "implementation_module": f"{c.PACKAGE_IMPORT}.solver_input_assembly",
            "implementation_function": "assemble_qubo_input",
            "test_vector_refs": ["PR162C-TEST-ALGORITHM-DELTA-QUBO_INPUT_ASSEMBLY_AUDIT-001"],
            "not_official_truth_if_non_official": False,
            "not_live_authority": True,
            "qtt_agent_consumer_route": ["QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"],
            "created_by_pr": c.PR_ID,
        },
    ]


def algorithm_test_vector_delta_records() -> list[dict[str, Any]]:
    return [
        {
            "test_vector_id": "PR162C-TEST-ALGORITHM-DELTA-STRICT_FIELD_COVERAGE_AUDIT-001",
            "algorithm_id": "PR162C-ALGORITHM-DELTA-STRICT_FIELD_COVERAGE_AUDIT",
            "inputs": {"required_fields": ["event_id", "market_id"], "provided_fields": ["market_id"]},
            "expected_output": {"missing_input_fields": ["event_id"], "coverage_status": "BLOCKED_REQUIRED_FIELDS_MISSING"},
            "tolerance": 0.0,
            "unit": "field_set",
            "edge_case_tests": [],
            "invalid_input_tests": [],
            "source_reference": SOURCE_LOCATORS["owner_pr162c"],
            "implementation_function_ref": f"{c.PACKAGE_IMPORT}.qku_field_coverage.strict_field_coverage_status",
            "implementation_module": f"{c.PACKAGE_IMPORT}.qku_field_coverage",
            "implementation_function": "strict_field_coverage_status",
            "created_by_pr": c.PR_ID,
        },
        {
            "test_vector_id": "PR162C-TEST-ALGORITHM-DELTA-QUBO_INPUT_ASSEMBLY_AUDIT-001",
            "algorithm_id": "PR162C-ALGORITHM-DELTA-QUBO_INPUT_ASSEMBLY_AUDIT",
            "inputs": {"variable_ids": ["x0", "x1"], "Q": [[2, 3], [0, 4]]},
            "expected_output": {
                "input_representation": "QUBO_MATRIX",
                "variable_ids": ["x0", "x1"],
                "term_count": 3,
                "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
            },
            "tolerance": 0.0,
            "unit": "solver_input_metadata",
            "edge_case_tests": [],
            "invalid_input_tests": [],
            "source_reference": SOURCE_LOCATORS["dwave_models"],
            "implementation_function_ref": f"{c.PACKAGE_IMPORT}.solver_input_assembly.assemble_qubo_input",
            "implementation_module": f"{c.PACKAGE_IMPORT}.solver_input_assembly",
            "implementation_function": "assemble_qubo_input",
            "created_by_pr": c.PR_ID,
        },
    ]


def execute_test_vector(record: dict[str, Any]) -> bool:
    module = importlib.import_module(record["implementation_module"])
    function = getattr(module, record["implementation_function"])
    observed = function(**record["inputs"])
    return _close(observed, record["expected_output"], float(record.get("tolerance", 1e-9)))


def _close(observed: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, float) or isinstance(observed, float):
        return math.isclose(float(observed), float(expected), rel_tol=tolerance, abs_tol=tolerance)
    if isinstance(expected, dict) and isinstance(observed, dict):
        return set(expected) == set(observed) and all(
            _close(observed[key], expected[key], tolerance) for key in expected
        )
    if isinstance(expected, list) and isinstance(observed, list):
        return len(expected) == len(observed) and all(
            _close(obs, exp, tolerance)
            for obs, exp in zip(observed, expected, strict=True)
        )
    return observed == expected


def _agents_for_family(family: str) -> list[str]:
    if family == "risk_sizing":
        return ["QTT_RISK_AGENT", "QTT_CAPITAL_AGENT", "QTT_PARAMETER_STACK_AGENT"]
    if family == "quantum_hybrid":
        return ["QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"]
    if family == "technical_feature":
        return ["QTT_REPLAY_AGENT", "QTT_PAPER_AGENT", "QTT_PARAMETER_STACK_AGENT"]
    if family == "prediction_market":
        return ["QTT_REPLAY_AGENT", "QTT_PAPER_AGENT", "QTT_EXECUTION_PREP_AGENT"]
    return ["QTT_RESEARCH_AGENT", "QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"]
