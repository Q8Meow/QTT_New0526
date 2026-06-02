"""Formula, objective, constraint, parameter, and test-vector registries."""

from __future__ import annotations

from collections.abc import Callable
import importlib
from typing import Any

from . import constants as c


SOURCE_LOCATORS = {
    "kalshi": "https://docs.kalshi.com/",
    "polymarket": "https://docs.polymarket.com/",
    "forecastex": "https://www.forecastex.com/",
    "sklearn": "https://scikit-learn.org/stable/modules/model_evaluation.html",
    "kelly": "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/portfolio-construction/key-concepts",
    "pypfopt": "https://pyportfolioopt.readthedocs.io/en/latest/",
    "scipy": "https://docs.scipy.org/doc/scipy/reference/optimize.html",
    "talib": "https://ta-lib.github.io/ta-lib-python/funcs.html",
    "pandas": "https://pandas.pydata.org/docs/",
    "numpy": "https://numpy.org/doc/stable/reference/routines.statistics.html",
    "dwave": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
    "qiskit": "https://qiskit-community.github.io/qiskit-optimization/",
    "ibm": "https://docs.quantum.ibm.com/",
}


def _function_path(module: str, function: str) -> tuple[str, str]:
    return (
        f"src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.{module}",
        function,
    )


def _spec(
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
    market_scope: str,
    test_inputs: dict[str, Any],
    expected_output: Any,
    *,
    tolerance: float = 1e-9,
    units: str = "unitless",
    variables: dict[str, str] | None = None,
    parameter_defaults: dict[str, Any] | None = None,
    parameter_ranges: dict[str, Any] | None = None,
    parameter_scales: dict[str, str] | None = None,
) -> dict[str, Any]:
    implementation_module, implementation_function = _function_path(module, function)
    formula_id = f"PR162B-FORMULA-{key.upper()}"
    return {
        "formula_id": formula_id,
        "formula_family": family,
        "formula_name": name,
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
        "normalization_policy": "caller supplies normalized numeric values",
        "missing_value_policy": "reject missing values before formula execution",
        "parameter_defaults": parameter_defaults or {},
        "parameter_ranges": parameter_ranges or {},
        "parameter_scales": parameter_scales or {},
        "source_class": source_class,
        "source_locator": source_locator,
        "source_evidence_required_flag": True,
        "authority_class": c.AUTHORITY_CLASS,
        "implementation_status": "IMPLEMENTED_DETERMINISTIC_PYTHON",
        "implementation_module": implementation_module,
        "implementation_function": implementation_function,
        "test_vector_refs": [f"PR162B-TEST-FORMULA-{key.upper()}-001"],
        "qku_refs": [],
        "agent_consumer_refs": [],
        "solver_mapping_refs": [],
        "primary_market_scope": market_scope,
        "compatible_market_scopes": _compatible_scopes(market_scope),
        "stage1_activation_status": "ACTIVE_STAGE1_REPLAY_PAPER_ONLY",
        "live_mode_status": "LIVE_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
        "replay_paper_required_flag": True,
        "owner_review_required_flag": True,
        "binding_proof_refs": [],
        "created_by_pr": c.PR_ID,
        "test_vector": {
            "test_vector_id": f"PR162B-TEST-FORMULA-{key.upper()}-001",
            "formula_id_or_algorithm_id": formula_id,
            "implementation_function": implementation_function,
            "implementation_module": implementation_module,
            "inputs": test_inputs,
            "expected_output": expected_output,
            "tolerance": tolerance,
            "unit": units,
            "edge_case_flag": False,
            "invalid_input_flag": False,
            "source_reference": source_locator,
            "test_status": "FORMULA_TEST_VECTOR_EXECUTED",
            "qku_refs": [],
        },
    }


def _compatible_scopes(primary: str) -> list[str]:
    if primary.startswith("PREDICTION_MARKET"):
        return [
            "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
            "PREDICTION_MARKET_MULTIOUTCOME_EVENT_CONTRACT",
            "PREDICTION_MARKET_SCALAR_RANGE_CONTRACT",
        ]
    if primary.startswith("MARKET_AGNOSTIC") or primary == "NON_MARKET_SPECIFIC":
        return list(c.STAGE1_ALLOWED_MARKET_SCOPES)
    return [primary]


def formula_specs() -> list[dict[str, Any]]:
    pm = "PREDICTION_MARKET_BINARY_EVENT_CONTRACT"
    math = "MARKET_AGNOSTIC_MATH"
    risk = "MARKET_AGNOSTIC_RISK"
    feature = "MARKET_AGNOSTIC_FEATURE"
    opt = "MARKET_AGNOSTIC_OPTIMIZER"
    quantum = "MARKET_AGNOSTIC_OPTIMIZER"
    return [
        _spec("implied_probability_from_binary_price", "prediction_market", "implied_probability_from_binary_price", "p = price", "Treats a normalized binary contract price as an implied probability candidate.", "prediction_market_formulas", "implied_probability_from_binary_price", ["price"], "implied_probability", "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE", SOURCE_LOCATORS["kalshi"], pm, {"price": 0.62}, 0.62),
        _spec("fair_price_from_probability", "prediction_market", "fair_price_from_probability", "price = p", "Maps a calibrated probability to a fair binary contract price candidate.", "prediction_market_formulas", "fair_price_from_probability", ["probability"], "fair_price", "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE", SOURCE_LOCATORS["polymarket"], pm, {"probability": 0.58}, 0.58),
        _spec("probability_edge", "prediction_market", "probability_edge", "edge = p_model - p_market", "Computes model probability edge over market implied probability.", "prediction_market_formulas", "probability_edge", ["model_probability", "market_probability"], "edge", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["forecastex"], pm, {"model_probability": 0.55, "market_probability": 0.5}, 0.05),
        _spec("expected_value_binary", "prediction_market", "expected_value_binary", "EV = p*w - (1-p)*l", "Computes binary expected value from win probability, profit if win, and loss if lose.", "prediction_market_formulas", "expected_value_binary", ["p_win", "profit_if_win", "loss_if_lose"], "expected_value", "TEXTBOOK_FORMULA_CANDIDATE", "https://en.wikipedia.org/wiki/Expected_value", pm, {"p_win": 0.55, "profit_if_win": 1.0, "loss_if_lose": 1.0}, 0.1),
        _spec("fee_adjusted_expected_value", "prediction_market", "fee_adjusted_expected_value", "EV_fee = EV - fee", "Subtracts a candidate fee cost from expected value.", "prediction_market_formulas", "fee_adjusted_expected_value", ["ev", "fee"], "fee_adjusted_ev", "OFFICIAL_API_DOC_FIELD_CANDIDATE", SOURCE_LOCATORS["kalshi"], pm, {"ev": 0.1, "fee": 0.01}, 0.09),
        _spec("slippage_adjusted_expected_value", "prediction_market", "slippage_adjusted_expected_value", "EV_slippage = EV - slippage", "Subtracts candidate slippage cost from expected value.", "prediction_market_formulas", "slippage_adjusted_expected_value", ["ev", "slippage_cost"], "slippage_adjusted_ev", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["scipy"], pm, {"ev": 0.1, "slippage_cost": 0.02}, 0.08),
        _spec("latency_adjusted_expected_value", "prediction_market", "latency_adjusted_expected_value", "EV_latency = EV - latency_penalty", "Subtracts candidate latency penalty from expected value.", "prediction_market_formulas", "latency_adjusted_expected_value", ["ev", "latency_penalty"], "latency_adjusted_ev", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["scipy"], pm, {"ev": 0.1, "latency_penalty": 0.03}, 0.07),
        _spec("expected_utility_candidate", "prediction_market", "expected_utility_candidate", "U = EV - risk_penalty", "Candidate risk-penalized expected utility.", "prediction_market_formulas", "expected_utility_candidate", ["expected_value", "risk_penalty"], "expected_utility", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], pm, {"expected_value": 0.12, "risk_penalty": 0.02}, 0.1),
        _spec("binary_payoff_profit_loss", "prediction_market", "binary_payoff_profit_loss", "PL = outcome*payout - price", "Computes candidate binary payoff profit/loss for a yes-style contract.", "prediction_market_formulas", "binary_payoff_profit_loss", ["outcome", "price_paid", "payout_if_win"], "profit_loss", "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE", SOURCE_LOCATORS["kalshi"], pm, {"outcome": 1, "price_paid": 0.4, "payout_if_win": 1.0}, 0.6),
        _spec("break_even_probability", "prediction_market", "break_even_probability", "p_be = (loss+cost)/(profit+loss)", "Computes break-even probability with candidate cost.", "prediction_market_formulas", "break_even_probability", ["cost", "profit_if_win", "loss_if_lose"], "break_even_probability", "TEXTBOOK_FORMULA_CANDIDATE", "https://en.wikipedia.org/wiki/Expected_value", pm, {"cost": 0.0, "profit_if_win": 1.0, "loss_if_lose": 1.0}, 0.5),
        _spec("no_trade_zone_threshold", "prediction_market", "no_trade_zone_threshold", "|edge| <= threshold", "Returns true when edge is inside the candidate no-trade zone.", "prediction_market_formulas", "no_trade_zone_threshold", ["edge", "threshold"], "inside_no_trade_zone", "OWNER_APPROVED_FORMULA_CANDIDATE", "OWNER_PR162B_SCOPE", pm, {"edge": 0.01, "threshold": 0.02}, True, units="boolean"),
        _spec("brier_score_binary", "calibration", "brier_score_binary", "(y-p)^2", "Binary Brier score for probabilistic predictions.", "calibration_formulas", "brier_score_binary", ["y_true", "p_pred"], "brier_score", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn"], math, {"y_true": 1, "p_pred": 0.8}, 0.04),
        _spec("log_loss_binary", "calibration", "log_loss_binary", "-log(p_y)", "Binary log-loss with probability clipping.", "calibration_formulas", "log_loss_binary", ["y_true", "p_pred", "epsilon"], "log_loss", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn"], math, {"y_true": 1, "p_pred": 0.8, "epsilon": 1e-15}, 0.2231435513142097),
        _spec("probability_clipping", "calibration", "probability_clipping", "clip(p, eps, 1-eps)", "Clips probabilities away from zero and one.", "calibration_formulas", "probability_clipping", ["probability", "epsilon"], "clipped_probability", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn"], math, {"probability": 0.0, "epsilon": 0.01}, 0.01),
        _spec("calibration_error_candidate", "calibration", "calibration_error_candidate", "|p_observed - p_predicted|", "Candidate absolute calibration error.", "calibration_formulas", "calibration_error_candidate", ["observed_probability", "predicted_probability"], "calibration_error", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn"], math, {"observed_probability": 0.7, "predicted_probability": 0.6}, 0.1),
        _spec("confidence_penalty_candidate", "calibration", "confidence_penalty_candidate", "w*(1-confidence)", "Candidate penalty for low confidence.", "calibration_formulas", "confidence_penalty_candidate", ["confidence", "penalty_weight"], "confidence_penalty", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["sklearn"], math, {"confidence": 0.8, "penalty_weight": 0.5}, 0.1),
        _spec("kelly_fraction", "position_sizing", "kelly_fraction", "(b*p-q)/b", "Binary Kelly fraction candidate.", "risk_position_sizing_formulas", "kelly_fraction_binary", ["p_win", "net_odds"], "kelly_fraction", "TEXTBOOK_FORMULA_CANDIDATE", SOURCE_LOCATORS["kelly"], risk, {"p_win": 0.55, "net_odds": 1.0}, 0.1),
        _spec("fractional_kelly", "position_sizing", "fractional_kelly", "f_fractional = f_kelly * fraction", "Scales Kelly by a conservative fraction.", "risk_position_sizing_formulas", "fractional_kelly", ["kelly_fraction", "fraction"], "fractional_kelly", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["kelly"], risk, {"kelly_fraction": 0.1, "fraction": 0.5}, 0.05),
        _spec("capped_kelly", "position_sizing", "capped_kelly", "min(max(f,-cap),cap)", "Caps a Kelly fraction candidate.", "risk_position_sizing_formulas", "capped_kelly", ["kelly_fraction", "cap"], "capped_kelly", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["kelly"], risk, {"kelly_fraction": 0.3, "cap": 0.2}, 0.2),
        _spec("risk_budget_capped_position_size", "position_sizing", "risk_budget_capped_position_size", "min(raw_size, risk_budget/unit_risk)", "Caps position size by candidate risk budget.", "risk_position_sizing_formulas", "risk_budget_capped_position_size", ["raw_size", "risk_budget", "unit_risk"], "position_size", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], risk, {"raw_size": 10, "risk_budget": 3, "unit_risk": 0.5}, 6.0),
        _spec("max_exposure_cap", "position_sizing", "max_exposure_cap", "clip(exposure, cap)", "Global candidate exposure cap.", "risk_position_sizing_formulas", "max_exposure_cap", ["requested_exposure", "max_exposure"], "exposure", "OWNER_APPROVED_FORMULA_CANDIDATE", "OWNER_PR162B_SCOPE", risk, {"requested_exposure": 12, "max_exposure": 5}, 5.0),
        _spec("per_market_cap", "position_sizing", "per_market_cap", "clip(exposure, market_cap)", "Per-market candidate exposure cap.", "risk_position_sizing_formulas", "per_market_cap", ["requested_exposure", "market_cap"], "market_exposure", "OWNER_APPROVED_FORMULA_CANDIDATE", "OWNER_PR162B_SCOPE", risk, {"requested_exposure": 4, "market_cap": 3}, 3.0),
        _spec("per_event_cap", "position_sizing", "per_event_cap", "clip(exposure, event_cap)", "Per-event candidate exposure cap.", "risk_position_sizing_formulas", "per_event_cap", ["requested_exposure", "event_cap"], "event_exposure", "OWNER_APPROVED_FORMULA_CANDIDATE", "OWNER_PR162B_SCOPE", risk, {"requested_exposure": 4, "event_cap": 2}, 2.0),
        _spec("mean_return", "risk_portfolio", "mean_return", "mean(x)", "Population mean of returns or values.", "risk_position_sizing_formulas", "mean_return", ["values"], "mean", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], risk, {"values": [1, 2, 3]}, 2.0),
        _spec("variance", "risk_portfolio", "variance", "E[(x-mean)^2]", "Population variance.", "risk_position_sizing_formulas", "variance", ["values"], "variance", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], risk, {"values": [1, 2, 3]}, 0.6666666666666666),
        _spec("covariance", "risk_portfolio", "covariance", "E[(x-mx)(y-my)]", "Population covariance.", "risk_position_sizing_formulas", "covariance", ["x", "y"], "covariance", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], risk, {"x": [1, 2, 3], "y": [1, 5, 7]}, 2.0),
        _spec("correlation", "risk_portfolio", "correlation", "cov(x,y)/(std_x*std_y)", "Population correlation.", "risk_position_sizing_formulas", "correlation", ["x", "y"], "correlation", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], risk, {"x": [1, 2, 3], "y": [1, 2, 3]}, 1.0),
        _spec("volatility", "risk_portfolio", "volatility", "sqrt(variance)", "Population standard deviation of returns.", "risk_position_sizing_formulas", "volatility", ["returns"], "volatility", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], risk, {"returns": [0.0, 0.1, -0.1]}, 0.08164965809277261),
        _spec("sharpe_ratio", "risk_portfolio", "sharpe_ratio", "(r-rf)/sigma", "Sharpe ratio candidate.", "risk_position_sizing_formulas", "sharpe_ratio", ["portfolio_return", "risk_free_rate", "volatility"], "sharpe_ratio", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], risk, {"portfolio_return": 0.12, "risk_free_rate": 0.02, "volatility": 0.2}, 0.5),
        _spec("max_drawdown", "risk_portfolio", "max_drawdown", "max((peak-equity)/peak)", "Maximum drawdown as a positive fraction.", "risk_position_sizing_formulas", "max_drawdown", ["equity_curve"], "max_drawdown", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], risk, {"equity_curve": [100, 120, 90, 130]}, 0.25),
        _spec("risk_adjusted_expected_value", "risk_portfolio", "risk_adjusted_expected_value", "EV - risk_penalty", "Risk-adjusted expected value candidate.", "risk_position_sizing_formulas", "risk_adjusted_expected_value", ["expected_value", "risk_penalty"], "risk_adjusted_ev", "INSTITUTIONAL_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], risk, {"expected_value": 0.12, "risk_penalty": 0.02}, 0.1),
        _spec("mean_variance_objective", "risk_portfolio", "mean_variance_objective", "mu - lambda*sigma^2", "Mean-variance objective candidate.", "portfolio_objectives", "mean_variance_objective", ["expected_return", "variance", "risk_aversion"], "objective_value", "OPEN_SOURCE_PACKAGE_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], opt, {"expected_return": 0.12, "variance": 0.04, "risk_aversion": 1.0}, 0.08),
        _spec("portfolio_qp_objective", "risk_portfolio", "portfolio_qp_objective", "w^T mu - lambda*w^T Sigma w", "Quadratic portfolio objective candidate.", "portfolio_objectives", "portfolio_qp_objective", ["weights", "returns", "covariance_matrix", "risk_aversion"], "objective_value", "OPEN_SOURCE_PACKAGE_FORMULA_CANDIDATE", SOURCE_LOCATORS["pypfopt"], opt, {"weights": [0.5, 0.5], "returns": [0.1, 0.2], "covariance_matrix": [[0.04, 0.0], [0.0, 0.09]], "risk_aversion": 1.0}, 0.1175),
        _spec("sma", "technical_feature", "SMA", "sum(x_window)/window", "Simple moving average.", "technical_feature_formulas", "simple_moving_average", ["values", "window"], "sma", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["talib"], feature, {"values": [1, 2, 3, 4], "window": 2}, 3.5),
        _spec("ema", "technical_feature", "EMA", "alpha*x_t + (1-alpha)*EMA_{t-1}", "Exponential moving average.", "technical_feature_formulas", "exponential_moving_average", ["values", "span"], "ema", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["pandas"], feature, {"values": [1, 2, 3], "span": 2}, 2.5555555555555554),
        _spec("rsi", "technical_feature", "RSI", "100 - 100/(1+RS)", "Relative Strength Index candidate.", "technical_feature_formulas", "rsi", ["values", "period"], "rsi", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["talib"], feature, {"values": [1, 2, 3, 2, 4], "period": 4}, 80.0),
        _spec("macd", "technical_feature", "MACD", "EMA_fast - EMA_slow", "MACD candidate with signal and histogram.", "technical_feature_formulas", "macd", ["values", "fast_span", "slow_span", "signal_span"], "macd", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["talib"], feature, {"values": [float(i) for i in range(1, 31)], "fast_span": 3, "slow_span": 6, "signal_span": 3}, {"macd": 1.499855382323247, "signal": 1.4997590101196496, "histogram": 9.637220359737242e-05}),
        _spec("bollinger_bands", "technical_feature", "Bollinger Bands", "SMA +/- k*std", "Bollinger band candidate.", "technical_feature_formulas", "bollinger_bands", ["values", "window", "num_std"], "bands", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["talib"], feature, {"values": [1, 2, 3, 4, 5], "window": 5, "num_std": 2.0}, {"lower": 0.1715728752538097, "middle": 3.0, "upper": 5.82842712474619}),
        _spec("z_score", "technical_feature", "z_score", "(x-mean)/std", "Standard score.", "technical_feature_formulas", "z_score", ["value", "mean", "std"], "z_score", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], feature, {"value": 12, "mean": 10, "std": 2}, 1.0),
        _spec("momentum", "technical_feature", "momentum", "x_t - x_{t-window}", "Price or feature momentum candidate.", "technical_feature_formulas", "momentum", ["values", "window"], "momentum", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["talib"], feature, {"values": [1, 3, 6], "window": 2}, 5.0),
        _spec("realized_volatility", "technical_feature", "realized_volatility", "sqrt(var(returns))*sqrt(annualization)", "Realized volatility candidate.", "technical_feature_formulas", "realized_volatility", ["returns", "annualization_factor"], "realized_volatility", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["numpy"], feature, {"returns": [0.0, 0.1, -0.1], "annualization_factor": 1.0}, 0.08164965809277261),
        _spec("vwap_candidate", "technical_feature", "VWAP_candidate", "sum(price*volume)/sum(volume)", "Volume-weighted average price candidate.", "technical_feature_formulas", "vwap", ["prices", "volumes"], "vwap", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["pandas"], feature, {"prices": [1, 2], "volumes": [2, 1]}, 1.3333333333333333),
        _spec("midpoint", "technical_feature", "midpoint", "(ask+bid)/2", "Bid-ask midpoint.", "technical_feature_formulas", "midpoint", ["ask", "bid"], "midpoint", "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE", SOURCE_LOCATORS["kalshi"], pm, {"ask": 0.6, "bid": 0.4}, 0.5),
        _spec("spread", "technical_feature", "spread", "ask-bid", "Bid-ask spread.", "technical_feature_formulas", "spread", ["ask", "bid"], "spread", "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE", SOURCE_LOCATORS["kalshi"], pm, {"ask": 0.6, "bid": 0.4}, 0.2),
        _spec("orderbook_imbalance_candidate", "technical_feature", "orderbook_imbalance_candidate", "(bid_size-ask_size)/(bid_size+ask_size)", "Order-book imbalance candidate.", "technical_feature_formulas", "orderbook_imbalance_candidate", ["bid_size", "ask_size"], "imbalance", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket"], pm, {"bid_size": 60, "ask_size": 40}, 0.2),
        _spec("liquidity_proxy_candidate", "technical_feature", "liquidity_proxy_candidate", "volume/max(spread,epsilon)", "Candidate liquidity proxy.", "technical_feature_formulas", "liquidity_proxy_candidate", ["volume", "spread_value", "epsilon"], "liquidity_proxy", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["polymarket"], pm, {"volume": 100, "spread_value": 0.5, "epsilon": 1e-9}, 200.0),
        _spec("qubo_objective_xtqx", "quantum_hybrid", "QUBO objective x^T Q x", "x^T Q x", "QUBO energy for binary vector and square Q matrix.", "quantum_formulations", "qubo_energy", ["x", "Q"], "qubo_energy", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["dwave"], quantum, {"x": [1, 0], "Q": [[2, 3], [0, 4]]}, 2.0),
        _spec("expanded_qubo_terms", "quantum_hybrid", "expanded QUBO terms", "sum_i sum_j Q_ij x_i x_j", "Expands non-zero QUBO terms.", "quantum_formulations", "expanded_qubo_terms", ["Q"], "terms", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["dwave"], quantum, {"Q": [[2, 0], [0, 4]]}, [{"i": 0, "j": 0, "coefficient": 2.0, "term": "x_0*x_0"}, {"i": 1, "j": 1, "coefficient": 4.0, "term": "x_1*x_1"}]),
        _spec("ising_energy", "quantum_hybrid", "Ising energy", "sum h_i s_i + sum J_ij s_i s_j", "Ising energy for spins and couplers.", "quantum_formulations", "ising_energy", ["spins", "h", "J"], "ising_energy", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["dwave"], quantum, {"spins": [1, -1], "h": [1.0, -0.5], "J": [(0, 1, 0.25)]}, 1.25),
        _spec("bqm_energy", "quantum_hybrid", "BQM energy", "linear + quadratic binary energy", "Binary quadratic model energy candidate.", "quantum_formulations", "bqm_energy", ["x", "linear", "quadratic"], "bqm_energy", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["dwave"], quantum, {"x": [1, 1], "linear": [1.0, 2.0], "quadratic": [(0, 1, 3.0)]}, 6.0),
        _spec("cqm_objective_constraints", "quantum_hybrid", "CQM objective and constraints", "objective + lambda*sum(v_i^2)", "Constrained quadratic model penalty assembly candidate.", "quantum_formulations", "cqm_objective_and_constraints", ["objective_value", "constraint_violations", "penalty_lambda"], "cqm_value", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["dwave"], quantum, {"objective_value": 1.0, "constraint_violations": [2.0], "penalty_lambda": 3.0}, 13.0),
        _spec("binary_penalty_constraint", "quantum_hybrid", "binary penalty constraint lambda(Ax-b)^2", "lambda*(Ax-b)^2", "Penalty constraint used for QUBO conversion.", "quantum_formulations", "binary_penalty_constraint", ["Ax_minus_b", "lambda_penalty"], "penalty", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["qiskit"], quantum, {"Ax_minus_b": 2.0, "lambda_penalty": 3.0}, 12.0),
        _spec("qubo_portfolio_selection_objective", "quantum_hybrid", "QUBO portfolio selection objective", "lambda*risk - return", "Builds a candidate QUBO matrix for portfolio selection.", "quantum_formulations", "qubo_portfolio_selection_objective", ["expected_returns", "risk_matrix", "risk_aversion"], "Q", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["qiskit"], quantum, {"expected_returns": [0.1, 0.2], "risk_matrix": [[1, 0], [0, 1]], "risk_aversion": 1.0}, [[0.9, 0.0], [0.0, 0.8]]),
        _spec("qubo_prediction_market_position_selection_objective", "quantum_hybrid", "QUBO prediction-market position selection objective", "risk_penalty - edge", "Builds a diagonal QUBO for prediction-market position selection.", "quantum_formulations", "qubo_prediction_market_position_selection_objective", ["edges", "risk_penalties"], "Q", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["qiskit"], quantum, {"edges": [0.1, 0.2], "risk_penalties": [0.3, 0.4]}, [[0.19999999999999998, 0.0], [0.0, 0.2]]),
        _spec("qubo_market_bundle_selection_objective", "quantum_hybrid", "QUBO market-bundle selection objective", "-score_i x_i", "Builds a diagonal market-bundle selection QUBO.", "quantum_formulations", "qubo_market_bundle_selection_objective", ["scores"], "Q", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["qiskit"], quantum, {"scores": [1.0, 2.0]}, [[-1.0, 0.0], [0.0, -2.0]]),
        _spec("qubo_parameter_stack_selection_objective", "quantum_hybrid", "QUBO parameter-stack selection objective", "penalty_i - score_i", "Builds a diagonal parameter-stack selection QUBO.", "quantum_formulations", "qubo_parameter_stack_selection_objective", ["scores", "penalties"], "Q", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["qiskit"], quantum, {"scores": [1.0, 2.0], "penalties": [0.1, 0.2]}, [[-0.9, 0.0], [0.0, -1.8]]),
        _spec("qubo_risk_budget_objective", "quantum_hybrid", "QUBO risk-budget objective", "lambda*exposure_i*exposure_j/budget", "Builds a candidate risk-budget QUBO.", "quantum_formulations", "qubo_risk_budget_objective", ["exposures", "budget", "penalty_lambda"], "Q", "RESEARCH_FORMULA_CANDIDATE", SOURCE_LOCATORS["qiskit"], quantum, {"exposures": [1.0, 2.0], "budget": 2.0, "penalty_lambda": 1.0}, [[0.5, 1.0], [1.0, 2.0]]),
        _spec("qaoa_hamiltonian_mapping_candidate", "quantum_hybrid", "QAOA Hamiltonian mapping candidate", "QUBO -> Ising Hamiltonian candidate", "Assembles QAOA Hamiltonian mapping metadata without backend execution.", "quantum_formulations", "qaoa_hamiltonian_mapping_candidate", ["Q"], "hamiltonian_mapping", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["ibm"], quantum, {"Q": [[1, 0], [0, 2]]}, {"hamiltonian_family": "QAOA_QUBO_TO_ISING_CANDIDATE", "term_count": 2, "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE"}),
        _spec("vqe_objective_candidate", "quantum_hybrid", "VQE objective candidate", "sum c_i <H_i>", "Computes a local VQE-style expectation value candidate.", "quantum_formulations", "vqe_objective_candidate", ["hamiltonian_terms", "expectation_values"], "vqe_objective", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["ibm"], quantum, {"hamiltonian_terms": [1.0, 2.0], "expectation_values": [0.5, 0.25]}, 1.0),
        _spec("annealing_bqm_cqm_candidate", "quantum_hybrid", "annealing BQM/CQM candidate", "QUBO -> BQM/CQM candidate", "Assembles annealing candidate metadata without backend execution.", "quantum_formulations", "annealing_bqm_cqm_candidate", ["Q"], "annealing_candidate", "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE", SOURCE_LOCATORS["dwave"], quantum, {"Q": [[1, 0], [0, 2]]}, {"input_representation": "BQM_OR_CQM_CANDIDATE", "variable_count": 2, "term_count": 2, "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE"}),
        _spec("hybrid_classical_quantum_comparator_objective", "quantum_hybrid", "hybrid classical-quantum comparator objective", "quantum_score - classical_score", "Local comparator objective candidate.", "quantum_formulations", "hybrid_classical_quantum_comparator_objective", ["classical_score", "quantum_candidate_score"], "score_delta", "REPO_EXISTING_FORMULA", "docs/master_plan/generated/PR162_QuantumClassicalHybridComparatorBlueprint.report.json", quantum, {"classical_score": 0.5, "quantum_candidate_score": 0.7}, 0.2),
    ]


def get_callable(module_path: str, function_name: str) -> Callable[..., Any]:
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    if not callable(function):
        raise TypeError(f"{module_path}.{function_name} is not callable")
    return function


def formula_records() -> list[dict[str, Any]]:
    return [{key: value for key, value in spec.items() if key != "test_vector"} for spec in formula_specs()]


def formula_test_vector_records() -> list[dict[str, Any]]:
    return [dict(spec["test_vector"]) for spec in formula_specs()]


def objective_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = {
        "mean_variance_objective",
        "portfolio_qp_objective",
        "QUBO objective x^T Q x",
        "QUBO portfolio selection objective",
        "QUBO prediction-market position selection objective",
        "QAOA Hamiltonian mapping candidate",
        "VQE objective candidate",
        "hybrid classical-quantum comparator objective",
    }
    output = []
    for formula in formulas:
        if formula["formula_name"] in names:
            output.append(
                {
                    "objective_id": formula["formula_id"].replace("FORMULA", "OBJECTIVE"),
                    "formula_ref": formula["formula_id"],
                    "objective_family": formula["formula_family"],
                    "objective_name": formula["formula_name"],
                    "mathematical_expression_latex": formula["mathematical_expression_latex"],
                    "input_fields": formula["input_fields"],
                    "output_fields": formula["output_fields"],
                    "source_class": formula["source_class"],
                    "source_locator": formula["source_locator"],
                    "implementation_status": formula["implementation_status"],
                    "implementation_module": formula["implementation_module"],
                    "implementation_function": formula["implementation_function"],
                    "qku_refs": list(formula["qku_refs"]),
                    "test_vector_refs": list(formula["test_vector_refs"]),
                    "created_by_pr": c.PR_ID,
                }
            )
    return output


def constraint_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = {
        "no_trade_zone_threshold",
        "max_exposure_cap",
        "per_market_cap",
        "per_event_cap",
        "binary penalty constraint lambda(Ax-b)^2",
        "CQM objective and constraints",
    }
    output = []
    for formula in formulas:
        if formula["formula_name"] in names:
            output.append(
                {
                    "constraint_id": formula["formula_id"].replace("FORMULA", "CONSTRAINT"),
                    "formula_ref": formula["formula_id"],
                    "constraint_family": formula["formula_family"],
                    "constraint_name": formula["formula_name"],
                    "input_fields": formula["input_fields"],
                    "output_fields": formula["output_fields"],
                    "source_class": formula["source_class"],
                    "source_locator": formula["source_locator"],
                    "implementation_status": formula["implementation_status"],
                    "implementation_module": formula["implementation_module"],
                    "implementation_function": formula["implementation_function"],
                    "qku_refs": list(formula["qku_refs"]),
                    "test_vector_refs": list(formula["test_vector_refs"]),
                    "created_by_pr": c.PR_ID,
                }
            )
    return output


PARAMETER_VALUE_SPECS = (
    ("minimum_edge_threshold_candidate", 0.02, [0.0, 0.2], "probability", "linear"),
    ("probability_clip_epsilon_candidate", 1e-6, [1e-15, 0.01], "probability", "log"),
    ("fractional_kelly_fraction_candidate", 0.25, [0.0, 1.0], "fraction", "linear"),
    ("max_kelly_cap_candidate", 0.1, [0.0, 0.5], "fraction", "linear"),
    ("per_market_exposure_cap_candidate", 0.05, [0.0, 1.0], "fraction_of_capital", "linear"),
    ("per_event_exposure_cap_candidate", 0.1, [0.0, 1.0], "fraction_of_capital", "linear"),
    ("max_position_size_candidate", 1.0, [0.0, 100.0], "contracts", "linear"),
    ("no_trade_zone_width_candidate", 0.01, [0.0, 0.1], "probability", "linear"),
    ("slippage_cost_candidate", 0.005, [0.0, 0.1], "currency", "linear"),
    ("fee_cost_candidate", 0.005, [0.0, 0.1], "currency", "linear"),
    ("latency_penalty_candidate", 0.002, [0.0, 0.1], "expected_value", "linear"),
    ("QUBO_penalty_lambda_candidate", 10.0, [1.0, 100.0], "penalty_weight", "log"),
    ("Ising_coefficient_scale_candidate", 1.0, [0.01, 100.0], "scale", "log"),
    ("QAOA_reps_candidate", 1, [1, 5], "count", "integer"),
    ("QAOA_shot_budget_candidate", 1024, [128, 8192], "shots", "integer"),
    ("annealing_reads_candidate", 100, [10, 1000], "reads", "integer"),
    ("smoke_solver_max_variables", 12, [1, 12], "binary_variables", "integer"),
    ("live_snapshot_ttl_candidate", 2.0, [0.1, 60.0], "seconds", "linear"),
    ("stale_snapshot_blocker_candidate", True, [False, True], "boolean", "boolean"),
)


def parameter_value_records(qku_refs: list[str] | None = None) -> list[dict[str, Any]]:
    refs = qku_refs or []
    records = []
    for index, (name, value, value_range, unit, scale) in enumerate(PARAMETER_VALUE_SPECS, start=1):
        records.append(
            {
                "parameter_id": f"PR162B-PARAMETER-VALUE-{index:03d}",
                "parameter_name": name,
                "candidate_value": value,
                "candidate_range": value_range,
                "unit": unit,
                "scale": scale,
                "formula_refs": [],
                "algorithm_refs": [],
                "qku_refs": refs[:1],
                "source_class": "OWNER_APPROVED_FORMULA_CANDIDATE",
                "source_locator": "OWNER_PR162B_SCOPE",
                "authority_class": c.AUTHORITY_CLASS,
                "replay_paper_required_flag": True,
                "owner_review_required_flag": True,
                "live_use_allowed_flag": False,
                "created_by_pr": c.PR_ID,
            }
        )
    return records


def parameter_range_scale_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "parameter_range_scale_id": record["parameter_id"].replace("VALUE", "RANGE-SCALE"),
            "parameter_id": record["parameter_id"],
            "parameter_name": record["parameter_name"],
            "candidate_range": record["candidate_range"],
            "unit": record["unit"],
            "scale": record["scale"],
            "source_class": record["source_class"],
            "source_locator": record["source_locator"],
            "authority_class": record["authority_class"],
            "live_use_allowed_flag": False,
            "created_by_pr": c.PR_ID,
        }
        for record in parameters
    ]


def tradable_value_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for record in parameters:
        output.append(
            {
                "tradable_value_id": record["parameter_id"].replace("PARAMETER-VALUE", "TRADABLE-VALUE"),
                "value_name": record["parameter_name"],
                "value_family": "candidate_parameter_value",
                "candidate_value": record["candidate_value"],
                "candidate_range": record["candidate_range"],
                "unit": record["unit"],
                "scale": record["scale"],
                "applies_to_market_scope": list(c.STAGE1_ALLOWED_MARKET_SCOPES),
                "formula_refs": record["formula_refs"],
                "algorithm_refs": record["algorithm_refs"],
                "qku_refs": record["qku_refs"],
                "agent_consumer_refs": [
                    "QTT_PARAMETER_STACK_AGENT",
                    "QTT_RISK_AGENT",
                    "QTT_CAPITAL_AGENT",
                ],
                "source_class": record["source_class"],
                "source_locator": record["source_locator"],
                "authority_class": record["authority_class"],
                "replay_paper_required_flag": True,
                "owner_review_required_flag": True,
                "live_use_allowed_flag": False,
                "blocker_code_if_unverified": "PR162B_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
                "created_by_pr": c.PR_ID,
            }
        )
    return output
