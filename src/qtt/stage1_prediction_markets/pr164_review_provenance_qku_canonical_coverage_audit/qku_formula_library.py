"""Executable PR164 formula library."""

from __future__ import annotations

from typing import Any, Callable


FormulaFn = Callable[[dict[str, Any]], dict[str, Any]]


def _num(inputs: dict[str, Any], key: str) -> float:
    return float(inputs[key])


def _seq(inputs: dict[str, Any], key: str) -> list[float]:
    return [float(value) for value in inputs[key]]


def binary_yes_event_ev(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "p_model")
        * (1.0 - _num(inputs, "ask_yes") - _num(inputs, "fee_per_contract") - _num(inputs, "settlement_cost"))
        - (1.0 - _num(inputs, "p_model"))
        * (_num(inputs, "ask_yes") + _num(inputs, "fee_per_contract") + _num(inputs, "settlement_cost"))
    )
    return {"EV_yes": value}


def binary_no_event_ev(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        (1.0 - _num(inputs, "p_model"))
        * (1.0 - _num(inputs, "ask_no") - _num(inputs, "fee_per_contract") - _num(inputs, "settlement_cost"))
        - _num(inputs, "p_model")
        * (_num(inputs, "ask_no") + _num(inputs, "fee_per_contract") + _num(inputs, "settlement_cost"))
    )
    return {"EV_no": value}


def complement_arbitrage(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        1.0
        - _num(inputs, "ask_yes")
        - _num(inputs, "ask_no")
        - _num(inputs, "fee_yes")
        - _num(inputs, "fee_no")
        - _num(inputs, "slippage_cost")
        - _num(inputs, "latency_cost")
    )
    return {"edge_complement": value}


def multi_outcome_probability_sum_rebalancing(inputs: dict[str, Any]) -> dict[str, float]:
    edge_buy_all = (
        1.0
        - sum(_seq(inputs, "ask_prices"))
        - _num(inputs, "total_fee_cost")
        - _num(inputs, "slippage_cost")
        - _num(inputs, "capital_lock_cost")
    )
    edge_sell_all = (
        sum(_seq(inputs, "bid_prices"))
        - 1.0
        - _num(inputs, "total_fee_cost")
        - _num(inputs, "execution_failure_penalty")
    )
    return {"edge_buy_all": edge_buy_all, "edge_sell_all": edge_sell_all}


def cross_venue_normalized_event_divergence(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "normalized_probability_A")
        - _num(inputs, "normalized_probability_B")
        - _num(inputs, "fee_A")
        - _num(inputs, "fee_B")
        - _num(inputs, "latency_cost")
        - _num(inputs, "transfer_or_settlement_cost")
        - _num(inputs, "execution_failure_penalty")
    )
    return {"edge_cross_venue": value}


def maker_spread_capture_candidate(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "edge_after_fees")
        + _num(inputs, "maker_spread_capture")
        - _num(inputs, "adverse_selection_cost")
        - _num(inputs, "queue_nonfill_penalty")
        - _num(inputs, "cancel_replace_cost")
    )
    return {"EV_maker": value}


def taker_crossing_candidate(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "edge_after_fees")
        - _num(inputs, "spread_crossing_cost")
        - _num(inputs, "slippage_cost")
        - _num(inputs, "latency_adverse_selection_cost")
    )
    return {"EV_taker": value}


def latency_adjusted_edge(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "raw_edge")
        - _num(inputs, "expected_price_move_per_ms") * _num(inputs, "latency_ms")
        - _num(inputs, "stale_data_penalty")
    )
    return {"latency_adjusted_edge": value}


def capital_lock_adjusted_edge(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "raw_edge")
        - _num(inputs, "locked_capital")
        * _num(inputs, "capital_lock_rate")
        * _num(inputs, "time_to_resolution_fraction")
    )
    return {"capital_lock_adjusted_edge": value}


def risk_adjusted_candidate_score(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "expected_net_profit_candidate")
        - _num(inputs, "drawdown_penalty")
        - _num(inputs, "tail_loss_penalty")
        - _num(inputs, "liquidity_penalty")
        - _num(inputs, "model_uncertainty_penalty")
        - _num(inputs, "source_uncertainty_penalty")
    )
    return {"risk_adjusted_candidate_score": value}


def fractional_kelly_candidate_sizing(inputs: dict[str, Any]) -> dict[str, float]:
    raw = (
        _num(inputs, "p_win") * _num(inputs, "payoff_multiple")
        - _num(inputs, "p_loss")
    ) / _num(inputs, "payoff_multiple")
    capped = max(
        0.0,
        min(
            _num(inputs, "owner_policy_cap"),
            _num(inputs, "risk_cap"),
            raw * _num(inputs, "fractional_kelly_multiplier"),
        ),
    )
    return {"kelly_fraction_raw": raw, "kelly_fraction_capped": capped}


def qubo_cqm_candidate_objective_mapping(inputs: dict[str, Any]) -> dict[str, Any]:
    expected = _seq(inputs, "expected_net_profit")
    return {
        "decision_variable": "x_i",
        "objective_direction": "maximize",
        "objective_terms_count": len(expected),
        "constraint_terms": [
            "capital",
            "event_exposure",
            "venue_exposure",
            "liquidity",
            "latency",
            "mutually_exclusive_outcomes",
        ],
        "quantum_backend_execution_allowed_flag": False,
        "quantum_advantage_claim_allowed_flag": False,
    }


FORMULA_SPECS: tuple[dict[str, Any], ...] = (
    {
        "formula_id": "PR164_FORMULA::BINARY_YES_EV",
        "formula_name": "Binary YES event expected value",
        "qku_family": "expected_value_probability_edge",
        "function": binary_yes_event_ev,
        "input_schema": {"p_model": "number[0,1]", "ask_yes": "number[0,1]", "fee_per_contract": "number", "settlement_cost": "number"},
        "output_schema": {"EV_yes": "number"},
        "parameter_schema": {"settlement_cost": "nonnegative decimal candidate value"},
        "formula_expression": "EV_yes = p_model * (1 - ask_yes - fee_per_contract - settlement_cost) - (1 - p_model) * (ask_yes + fee_per_contract + settlement_cost)",
        "objective_expression": "maximize EV_yes net of execution cost and risk penalty for replay/paper candidate review",
        "test_vector": {"p_model": 0.62, "ask_yes": 0.51, "fee_per_contract": 0.01, "settlement_cost": 0.005},
        "expected_output": {"EV_yes": 0.095},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_EXPECTED_VALUE_MATERIALIZER",
        "agent_consumer": "formula_objective_solver_agent",
        "quantum_mapping_hint": "CQM objective term candidate",
    },
    {
        "formula_id": "PR164_FORMULA::BINARY_NO_EV",
        "formula_name": "Binary NO event expected value",
        "qku_family": "expected_value_probability_edge",
        "function": binary_no_event_ev,
        "input_schema": {"p_model": "number[0,1]", "ask_no": "number[0,1]", "fee_per_contract": "number", "settlement_cost": "number"},
        "output_schema": {"EV_no": "number"},
        "parameter_schema": {"settlement_cost": "nonnegative decimal candidate value"},
        "formula_expression": "EV_no = (1 - p_model) * (1 - ask_no - fee_per_contract - settlement_cost) - p_model * (ask_no + fee_per_contract + settlement_cost)",
        "objective_expression": "maximize EV_no net of execution cost and risk penalty for replay/paper candidate review",
        "test_vector": {"p_model": 0.62, "ask_no": 0.42, "fee_per_contract": 0.01, "settlement_cost": 0.005},
        "expected_output": {"EV_no": -0.055},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_EXPECTED_VALUE_MATERIALIZER",
        "agent_consumer": "formula_objective_solver_agent",
        "quantum_mapping_hint": "CQM objective term candidate",
    },
    {
        "formula_id": "PR164_FORMULA::COMPLEMENT_ARBITRAGE",
        "formula_name": "Complement arbitrage",
        "qku_family": "expected_value_probability_edge",
        "function": complement_arbitrage,
        "input_schema": {"ask_yes": "number", "ask_no": "number", "fee_yes": "number", "fee_no": "number", "slippage_cost": "number", "latency_cost": "number"},
        "output_schema": {"edge_complement": "number"},
        "parameter_schema": {"latency_cost": "nonnegative decimal candidate value"},
        "formula_expression": "edge_complement = 1 - ask_yes - ask_no - fee_yes - fee_no - slippage_cost - latency_cost",
        "objective_expression": "maximize positive complement edge for replay/paper candidate routing",
        "test_vector": {"ask_yes": 0.45, "ask_no": 0.48, "fee_yes": 0.01, "fee_no": 0.01, "slippage_cost": 0.005, "latency_cost": 0.002},
        "expected_output": {"edge_complement": 0.043},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_ARBITRAGE_MATERIALIZER",
        "agent_consumer": "formula_objective_solver_agent",
        "quantum_mapping_hint": "binary inclusion variable candidate",
    },
    {
        "formula_id": "PR164_FORMULA::MULTIOUTCOME_REBALANCING",
        "formula_name": "Multi-outcome probability-sum rebalancing",
        "qku_family": "expected_value_probability_edge",
        "function": multi_outcome_probability_sum_rebalancing,
        "input_schema": {"ask_prices": "array[number]", "bid_prices": "array[number]", "total_fee_cost": "number", "slippage_cost": "number", "capital_lock_cost": "number", "execution_failure_penalty": "number"},
        "output_schema": {"edge_buy_all": "number", "edge_sell_all": "number"},
        "parameter_schema": {"execution_failure_penalty": "nonnegative decimal candidate value"},
        "formula_expression": "edge_buy_all = 1 - sum(ask_prices) - total_fee_cost - slippage_cost - capital_lock_cost; edge_sell_all = sum(bid_prices) - 1 - total_fee_cost - execution_failure_penalty",
        "objective_expression": "maximize buy-all or sell-all edge after execution-cost components",
        "test_vector": {"ask_prices": [0.2, 0.3, 0.4], "bid_prices": [0.22, 0.31, 0.42], "total_fee_cost": 0.03, "slippage_cost": 0.01, "capital_lock_cost": 0.005, "execution_failure_penalty": 0.02},
        "expected_output": {"edge_buy_all": 0.055, "edge_sell_all": -0.1},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_ARBITRAGE_MATERIALIZER",
        "agent_consumer": "formula_objective_solver_agent",
        "quantum_mapping_hint": "DQM/CQM multi-outcome candidate",
    },
    {
        "formula_id": "PR164_FORMULA::CROSS_VENUE_DIVERGENCE",
        "formula_name": "Cross-venue normalized event divergence",
        "qku_family": "probability_calibration_edge",
        "function": cross_venue_normalized_event_divergence,
        "input_schema": {"normalized_probability_A": "number", "normalized_probability_B": "number", "fee_A": "number", "fee_B": "number", "latency_cost": "number", "transfer_or_settlement_cost": "number", "execution_failure_penalty": "number"},
        "output_schema": {"edge_cross_venue": "number"},
        "parameter_schema": {"transfer_or_settlement_cost": "nonnegative decimal candidate value"},
        "formula_expression": "edge_cross_venue = normalized_probability_A - normalized_probability_B - fee_A - fee_B - latency_cost - transfer_or_settlement_cost - execution_failure_penalty",
        "objective_expression": "maximize cross-venue edge only in replay/paper candidate lanes",
        "test_vector": {"normalized_probability_A": 0.64, "normalized_probability_B": 0.59, "fee_A": 0.01, "fee_B": 0.01, "latency_cost": 0.003, "transfer_or_settlement_cost": 0.002, "execution_failure_penalty": 0.004},
        "expected_output": {"edge_cross_venue": 0.021},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_CROSS_VENUE_MATERIALIZER",
        "agent_consumer": "formula_objective_solver_agent",
        "quantum_mapping_hint": "CQM venue exposure constraint candidate",
    },
    {
        "formula_id": "PR164_FORMULA::MAKER_SPREAD_CAPTURE",
        "formula_name": "Maker spread capture candidate",
        "qku_family": "market_microstructure_liquidity",
        "function": maker_spread_capture_candidate,
        "input_schema": {"edge_after_fees": "number", "maker_spread_capture": "number", "adverse_selection_cost": "number", "queue_nonfill_penalty": "number", "cancel_replace_cost": "number"},
        "output_schema": {"EV_maker": "number"},
        "parameter_schema": {"queue_nonfill_penalty": "nonnegative decimal candidate value"},
        "formula_expression": "EV_maker = edge_after_fees + maker_spread_capture - adverse_selection_cost - queue_nonfill_penalty - cancel_replace_cost",
        "objective_expression": "maximize maker expected value net of queue, cancel, and adverse-selection costs",
        "test_vector": {"edge_after_fees": 0.04, "maker_spread_capture": 0.015, "adverse_selection_cost": 0.008, "queue_nonfill_penalty": 0.006, "cancel_replace_cost": 0.003},
        "expected_output": {"EV_maker": 0.038},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_TCA_MATERIALIZER",
        "agent_consumer": "tca_agent",
        "quantum_mapping_hint": "classical comparator candidate",
    },
    {
        "formula_id": "PR164_FORMULA::TAKER_CROSSING",
        "formula_name": "Taker crossing candidate",
        "qku_family": "market_microstructure_liquidity",
        "function": taker_crossing_candidate,
        "input_schema": {"edge_after_fees": "number", "spread_crossing_cost": "number", "slippage_cost": "number", "latency_adverse_selection_cost": "number"},
        "output_schema": {"EV_taker": "number"},
        "parameter_schema": {"latency_adverse_selection_cost": "nonnegative decimal candidate value"},
        "formula_expression": "EV_taker = edge_after_fees - spread_crossing_cost - slippage_cost - latency_adverse_selection_cost",
        "objective_expression": "maximize taker expected value net of crossing and adverse-selection costs",
        "test_vector": {"edge_after_fees": 0.06, "spread_crossing_cost": 0.012, "slippage_cost": 0.007, "latency_adverse_selection_cost": 0.005},
        "expected_output": {"EV_taker": 0.036},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_TCA_MATERIALIZER",
        "agent_consumer": "tca_agent",
        "quantum_mapping_hint": "classical comparator candidate",
    },
    {
        "formula_id": "PR164_FORMULA::LATENCY_ADJUSTED_EDGE",
        "formula_name": "Latency-adjusted edge",
        "qku_family": "latency_slippage_cost",
        "function": latency_adjusted_edge,
        "input_schema": {"raw_edge": "number", "expected_price_move_per_ms": "number", "latency_ms": "number", "stale_data_penalty": "number"},
        "output_schema": {"latency_adjusted_edge": "number"},
        "parameter_schema": {"latency_ms": "nonnegative decimal candidate value"},
        "formula_expression": "latency_adjusted_edge = raw_edge - expected_price_move_per_ms * latency_ms - stale_data_penalty",
        "objective_expression": "maximize latency-adjusted edge after stale-data penalty",
        "test_vector": {"raw_edge": 0.08, "expected_price_move_per_ms": 0.00002, "latency_ms": 250.0, "stale_data_penalty": 0.004},
        "expected_output": {"latency_adjusted_edge": 0.071},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_LATENCY_MATERIALIZER",
        "agent_consumer": "latency_agent",
        "quantum_mapping_hint": "latency penalty term candidate",
    },
    {
        "formula_id": "PR164_FORMULA::CAPITAL_LOCK_ADJUSTED_EDGE",
        "formula_name": "Capital-lock-adjusted edge",
        "qku_family": "risk_capital_sizing",
        "function": capital_lock_adjusted_edge,
        "input_schema": {"raw_edge": "number", "locked_capital": "number", "capital_lock_rate": "number", "time_to_resolution_fraction": "number"},
        "output_schema": {"capital_lock_adjusted_edge": "number"},
        "parameter_schema": {"capital_lock_rate": "nonnegative decimal candidate value"},
        "formula_expression": "capital_lock_adjusted_edge = raw_edge - locked_capital * capital_lock_rate * time_to_resolution_fraction",
        "objective_expression": "maximize edge after capital-lock cost",
        "test_vector": {"raw_edge": 0.05, "locked_capital": 1000.0, "capital_lock_rate": 0.1, "time_to_resolution_fraction": 0.25},
        "expected_output": {"capital_lock_adjusted_edge": -24.95},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_RISK_MATERIALIZER",
        "agent_consumer": "risk_agent",
        "quantum_mapping_hint": "capital penalty term candidate",
    },
    {
        "formula_id": "PR164_FORMULA::RISK_ADJUSTED_CANDIDATE_SCORE",
        "formula_name": "Risk-adjusted candidate score",
        "qku_family": "deterministic_candidate_ranking_algorithm",
        "function": risk_adjusted_candidate_score,
        "input_schema": {"expected_net_profit_candidate": "number", "drawdown_penalty": "number", "tail_loss_penalty": "number", "liquidity_penalty": "number", "model_uncertainty_penalty": "number", "source_uncertainty_penalty": "number"},
        "output_schema": {"risk_adjusted_candidate_score": "number"},
        "parameter_schema": {"model_uncertainty_penalty": "nonnegative decimal candidate value"},
        "formula_expression": "risk_adjusted_candidate_score = expected_net_profit_candidate - drawdown_penalty - tail_loss_penalty - liquidity_penalty - model_uncertainty_penalty - source_uncertainty_penalty",
        "objective_expression": "maximize risk-adjusted candidate score for PR165 scoring input",
        "test_vector": {"expected_net_profit_candidate": 25.0, "drawdown_penalty": 2.0, "tail_loss_penalty": 3.0, "liquidity_penalty": 1.5, "model_uncertainty_penalty": 4.0, "source_uncertainty_penalty": 0.5},
        "expected_output": {"risk_adjusted_candidate_score": 14.0},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_SCORING_MATERIALIZER",
        "agent_consumer": "risk_agent",
        "quantum_mapping_hint": "classical comparator objective candidate",
    },
    {
        "formula_id": "PR164_FORMULA::FRACTIONAL_KELLY_REPLAY_PAPER",
        "formula_name": "Fractional Kelly candidate sizing for replay/paper only",
        "qku_family": "risk_capital_sizing",
        "function": fractional_kelly_candidate_sizing,
        "input_schema": {"p_win": "number[0,1]", "p_loss": "number[0,1]", "payoff_multiple": "positive number", "owner_policy_cap": "number", "risk_cap": "number", "fractional_kelly_multiplier": "number"},
        "output_schema": {"kelly_fraction_raw": "number", "kelly_fraction_capped": "number"},
        "parameter_schema": {"owner_policy_cap": "candidate cap; no live sizing authority"},
        "formula_expression": "kelly_fraction_raw = (p_win * payoff_multiple - p_loss) / payoff_multiple; kelly_fraction_capped = max(0, min(owner_policy_cap, risk_cap, kelly_fraction_raw * fractional_kelly_multiplier))",
        "objective_expression": "produce replay/paper sizing candidate only; no live sizing authority",
        "test_vector": {"p_win": 0.6, "p_loss": 0.4, "payoff_multiple": 1.2, "owner_policy_cap": 0.2, "risk_cap": 0.15, "fractional_kelly_multiplier": 0.5},
        "expected_output": {"kelly_fraction_raw": 0.26666666666666666, "kelly_fraction_capped": 0.13333333333333333},
        "numerical_tolerance": 1.0e-9,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_RISK_MATERIALIZER",
        "agent_consumer": "risk_agent",
        "quantum_mapping_hint": "capital constraint comparator only",
    },
    {
        "formula_id": "PR164_FORMULA::QUBO_CQM_CANDIDATE_OBJECTIVE_MAPPING",
        "formula_name": "QUBO/CQM candidate objective mapping",
        "qku_family": "quantum_bundle_selection_optimizer",
        "function": qubo_cqm_candidate_objective_mapping,
        "input_schema": {"expected_net_profit": "array[number]", "lambda_risk": "number", "lambda_corr": "number", "lambda_latency": "number", "lambda_capital": "number", "lambda_source": "number"},
        "output_schema": {"decision_variable": "x_i", "objective_terms_count": "integer", "constraint_terms": "array[string]"},
        "parameter_schema": {"lambda_terms": "nonnegative penalty weights"},
        "formula_expression": "decision variable x_i = include candidate i; maximize sum(expected_net_profit_i * x_i) minus lambda_risk * portfolio_risk_terms minus lambda_corr * correlated_event_penalties minus lambda_latency * latency_cost_terms minus lambda_capital * capital_lock_terms minus lambda_source * source_uncertainty_terms subject to capital, event exposure, venue exposure, liquidity, latency, and mutually exclusive outcome constraints",
        "objective_expression": "map candidate structure to QUBO/CQM objective only; no quantum backend execution",
        "test_vector": {"expected_net_profit": [1.2, 0.8], "lambda_risk": 0.4, "lambda_corr": 0.3, "lambda_latency": 0.2, "lambda_capital": 0.5, "lambda_source": 0.1},
        "expected_output": {"decision_variable": "x_i", "objective_direction": "maximize", "objective_terms_count": 2, "constraint_terms": ["capital", "event_exposure", "venue_exposure", "liquidity", "latency", "mutually_exclusive_outcomes"], "quantum_backend_execution_allowed_flag": False, "quantum_advantage_claim_allowed_flag": False},
        "numerical_tolerance": 0.0,
        "replay_paper_consumer": "PR164_REPLAY_PAPER_QUANTUM_COMPARATOR_PREPARATION",
        "agent_consumer": "quantum_mapper_advisory_agent",
        "quantum_mapping_hint": "QUBO/BQM/CQM/BQM-compatible structure candidate",
    },
)

FORMULA_FUNCTIONS: dict[str, FormulaFn] = {
    str(spec["formula_id"]): spec["function"] for spec in FORMULA_SPECS
}


def registry_rows() -> list[dict[str, Any]]:
    rows = []
    for spec in FORMULA_SPECS:
        row = {key: value for key, value in spec.items() if key != "function"}
        row["function_ref"] = f"{__name__}:{spec['function'].__name__}"
        row["live_sizing_authority_created"] = False
        row["quantum_backend_execution_allowed_flag"] = False
        row["quantum_advantage_claim_allowed_flag"] = False
        rows.append(row)
    return rows
