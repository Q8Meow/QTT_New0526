"""Executable formula seed library for PR162D-R2A."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable


EPSILON = 1.0e-9
FormulaCallable = Callable[[dict[str, Any]], dict[str, Any]]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _num(inputs: dict[str, Any], key: str, default: float | None = None) -> float:
    if key in inputs:
        return float(inputs[key])
    if default is not None:
        return float(default)
    raise KeyError(key)


def _seq(inputs: dict[str, Any], key: str) -> list[float]:
    return [float(item) for item in inputs[key]]


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def compute_yes_ev(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "p_model") * _num(inputs, "payout")
        - _num(inputs, "yes_price")
        - _num(inputs, "fee_estimate")
        - _num(inputs, "slippage_estimate")
        - _num(inputs, "latency_cost_estimate")
    )
    return {"yes_ev": value}


def compute_no_ev(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        (1.0 - _num(inputs, "p_model")) * _num(inputs, "payout")
        - _num(inputs, "no_price")
        - _num(inputs, "fee_estimate")
        - _num(inputs, "slippage_estimate")
        - _num(inputs, "latency_cost_estimate")
    )
    return {"no_ev": value}


def compute_implied_probability(inputs: dict[str, Any]) -> dict[str, float]:
    value = clamp(_num(inputs, "price") / max(_num(inputs, "payout"), EPSILON), 0.0, 1.0)
    return {"implied_probability": value}


def compute_probability_edge(inputs: dict[str, Any]) -> dict[str, float]:
    return {"probability_edge": _num(inputs, "p_model") - _num(inputs, "implied_probability")}


def compute_net_edge(inputs: dict[str, Any]) -> dict[str, float]:
    return {"net_edge": _num(inputs, "expected_net_value") / max(_num(inputs, "entry_price"), EPSILON)}


def compute_mid_price(inputs: dict[str, Any]) -> dict[str, float]:
    return {"mid_price": (_num(inputs, "best_bid") + _num(inputs, "best_ask")) / 2.0}


def compute_spread(inputs: dict[str, Any]) -> dict[str, float]:
    return {"spread": _num(inputs, "best_ask") - _num(inputs, "best_bid")}


def compute_relative_spread(inputs: dict[str, Any]) -> dict[str, float]:
    return {"relative_spread": _num(inputs, "spread") / max(_num(inputs, "mid_price"), EPSILON)}


def compute_orderbook_imbalance(inputs: dict[str, Any]) -> dict[str, float]:
    bid_size = _num(inputs, "bid_size")
    ask_size = _num(inputs, "ask_size")
    return {"orderbook_imbalance": (bid_size - ask_size) / max(bid_size + ask_size, EPSILON)}


def compute_liquidity_score(inputs: dict[str, Any]) -> dict[str, float]:
    denominator = max(_num(inputs, "spread"), _num(inputs, "tick_size_or_epsilon", EPSILON), EPSILON)
    value = math.log1p(_num(inputs, "volume")) * math.log1p(_num(inputs, "depth")) / denominator
    return {"liquidity_score": value}


def compute_latency_cost(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        abs(_num(inputs, "price_velocity_per_second"))
        * _num(inputs, "expected_latency_seconds")
        * _num(inputs, "notional_sensitivity")
    )
    return {"latency_cost": value}


def compute_slippage_estimate(inputs: dict[str, Any]) -> dict[str, float]:
    return {
        "slippage_estimate": _num(inputs, "spread_component")
        + _num(inputs, "depth_impact_component")
        + _num(inputs, "volatility_impact_component")
    }


def compute_kelly_capped(inputs: dict[str, Any]) -> dict[str, float]:
    edge_probability = _num(inputs, "edge_probability")
    loss_probability = _num(inputs, "loss_probability")
    odds = _num(inputs, "odds_payoff_ratio")
    raw = (edge_probability * odds - loss_probability) / max(odds, EPSILON)
    return {"kelly_raw": raw, "kelly_capped": clamp(raw, 0.0, _num(inputs, "max_fraction_cap"))}


def compute_brier_score(inputs: dict[str, Any]) -> dict[str, float]:
    actual = _seq(inputs, "actual_outcomes")
    predicted = _seq(inputs, "predicted_probabilities")
    return {"brier_score": _mean([(a - p) ** 2 for a, p in zip(actual, predicted, strict=True)])}


def compute_log_loss(inputs: dict[str, Any]) -> dict[str, float]:
    actual = _seq(inputs, "actual_outcomes")
    predicted = [clamp(p, EPSILON, 1.0 - EPSILON) for p in _seq(inputs, "predicted_probabilities")]
    value = -_mean(
        [
            a * math.log(p) + (1.0 - a) * math.log(1.0 - p)
            for a, p in zip(actual, predicted, strict=True)
        ]
    )
    return {"log_loss": value}


def compute_ema(inputs: dict[str, Any]) -> dict[str, float]:
    alpha = _num(inputs, "alpha")
    return {"ema_t": alpha * _num(inputs, "price_t") + (1.0 - alpha) * _num(inputs, "ema_t_minus_1")}


def compute_simple_return(inputs: dict[str, Any]) -> dict[str, float]:
    return {"simple_return": _num(inputs, "price_t") / max(_num(inputs, "price_t_minus_1"), EPSILON) - 1.0}


def compute_rolling_volatility(inputs: dict[str, Any]) -> dict[str, float]:
    return {"rolling_volatility": _std(_seq(inputs, "returns_window"))}


def compute_vwap(inputs: dict[str, Any]) -> dict[str, float]:
    prices = _seq(inputs, "prices")
    volumes = _seq(inputs, "volumes")
    numerator = sum(price * volume for price, volume in zip(prices, volumes, strict=True))
    return {"vwap": numerator / max(sum(volumes), EPSILON)}


def compute_bollinger_z(inputs: dict[str, Any]) -> dict[str, float]:
    return {
        "bollinger_z": (
            _num(inputs, "price") - _num(inputs, "rolling_mean")
        )
        / max(_num(inputs, "rolling_std"), EPSILON)
    }


def compute_rsi(inputs: dict[str, Any]) -> dict[str, float]:
    deltas = _seq(inputs, "deltas")
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [abs(min(delta, 0.0)) for delta in deltas]
    rs = _mean(gains) / max(_mean(losses), EPSILON)
    return {"avg_gain": _mean(gains), "avg_loss": _mean(losses), "rs": rs, "rsi": 100.0 - 100.0 / (1.0 + rs)}


def compute_macd(inputs: dict[str, Any]) -> dict[str, float]:
    macd = _num(inputs, "ema_fast") - _num(inputs, "ema_slow")
    signal = _num(inputs, "signal_alpha") * macd + (1.0 - _num(inputs, "signal_alpha")) * _num(
        inputs, "macd_signal_t_minus_1"
    )
    return {"macd": macd, "macd_signal": signal, "macd_histogram": macd - signal}


def compute_risk_adjusted_score(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "expected_net_value")
        - _num(inputs, "drawdown_penalty_lambda") * _num(inputs, "drawdown_risk")
        - _num(inputs, "latency_penalty_lambda") * _num(inputs, "latency_cost")
        - _num(inputs, "slippage_penalty_lambda") * _num(inputs, "slippage_estimate")
        - _num(inputs, "complexity_penalty_lambda") * _num(inputs, "complexity_score")
    )
    return {"risk_adjusted_score": value}


def compute_candidate_selection_score(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "replay_value_score")
        + _num(inputs, "paper_value_score")
        + _num(inputs, "stability_score")
        + _num(inputs, "cross_market_generalization_score")
        + _num(inputs, "quantum_priority_boost")
        - _num(inputs, "latency_penalty")
        - _num(inputs, "drawdown_penalty")
        - _num(inputs, "data_missing_penalty")
        - _num(inputs, "complexity_penalty")
    )
    return {"candidate_selection_score": value}


def compute_depth_impact_component(inputs: dict[str, Any]) -> dict[str, float]:
    return {"depth_impact_component": _num(inputs, "order_size") / max(_num(inputs, "available_depth"), EPSILON)}


def compute_volatility_impact_component(inputs: dict[str, Any]) -> dict[str, float]:
    return {"volatility_impact_component": _num(inputs, "rolling_volatility") * math.sqrt(_num(inputs, "holding_period_seconds"))}


def compute_spread_component(inputs: dict[str, Any]) -> dict[str, float]:
    return {"spread_component": _num(inputs, "spread") * _num(inputs, "spread_capture_fraction")}


def compute_depth_weighted_mid_price(inputs: dict[str, Any]) -> dict[str, float]:
    bid_size = _num(inputs, "bid_size")
    ask_size = _num(inputs, "ask_size")
    value = (_num(inputs, "best_bid") * ask_size + _num(inputs, "best_ask") * bid_size) / max(
        bid_size + ask_size, EPSILON
    )
    return {"depth_weighted_mid_price": value}


def compute_top_of_book_depth(inputs: dict[str, Any]) -> dict[str, float]:
    return {"top_of_book_depth": _num(inputs, "bid_size") + _num(inputs, "ask_size")}


def compute_market_pressure(inputs: dict[str, Any]) -> dict[str, float]:
    return {"market_pressure": _num(inputs, "orderbook_imbalance") * _num(inputs, "relative_spread")}


def compute_volume_growth_rate(inputs: dict[str, Any]) -> dict[str, float]:
    return {"volume_growth_rate": _num(inputs, "volume_t") / max(_num(inputs, "volume_t_minus_1"), EPSILON) - 1.0}


def compute_candle_return(inputs: dict[str, Any]) -> dict[str, float]:
    return {"candle_return": _num(inputs, "close_price") / max(_num(inputs, "open_price"), EPSILON) - 1.0}


def compute_high_low_range(inputs: dict[str, Any]) -> dict[str, float]:
    return {"high_low_range": _num(inputs, "high_price") - _num(inputs, "low_price")}


def compute_candle_body(inputs: dict[str, Any]) -> dict[str, float]:
    return {"candle_body": abs(_num(inputs, "close_price") - _num(inputs, "open_price"))}


def compute_wick_ratio(inputs: dict[str, Any]) -> dict[str, float]:
    body = abs(_num(inputs, "close_price") - _num(inputs, "open_price"))
    candle_range = _num(inputs, "high_price") - _num(inputs, "low_price")
    return {"wick_ratio": (candle_range - body) / max(candle_range, EPSILON)}


def compute_realized_spread_proxy(inputs: dict[str, Any]) -> dict[str, float]:
    return {"realized_spread_proxy": abs(_num(inputs, "execution_price") - _num(inputs, "mid_price_after_delay"))}


def compute_momentum_n_period(inputs: dict[str, Any]) -> dict[str, float]:
    return {"momentum_n_period": _num(inputs, "price_t") - _num(inputs, "price_t_minus_n")}


def compute_price_zscore(inputs: dict[str, Any]) -> dict[str, float]:
    return {"price_zscore": (_num(inputs, "price") - _num(inputs, "mean_price")) / max(_num(inputs, "std_price"), EPSILON)}


def compute_sharpe_like_score(inputs: dict[str, Any]) -> dict[str, float]:
    return {"sharpe_like_score": _num(inputs, "mean_return") / max(_num(inputs, "return_volatility"), EPSILON)}


def compute_expected_shortfall_proxy(inputs: dict[str, Any]) -> dict[str, float]:
    losses = sorted([value for value in _seq(inputs, "losses") if value >= _num(inputs, "var_threshold")])
    return {"expected_shortfall_proxy": _mean(losses) if losses else 0.0}


def compute_capital_utilization(inputs: dict[str, Any]) -> dict[str, float]:
    return {"capital_utilization": _num(inputs, "capital_used") / max(_num(inputs, "capital_budget"), EPSILON)}


def compute_exposure_utilization(inputs: dict[str, Any]) -> dict[str, float]:
    return {"exposure_utilization": _num(inputs, "exposure_used") / max(_num(inputs, "max_exposure"), EPSILON)}


def compute_cost_to_budget_ratio(inputs: dict[str, Any]) -> dict[str, float]:
    return {"cost_to_budget_ratio": _num(inputs, "candidate_cost") / max(_num(inputs, "budget"), EPSILON)}


def compute_logit(inputs: dict[str, Any]) -> dict[str, float]:
    p_model = clamp(_num(inputs, "p_model"), EPSILON, 1.0 - EPSILON)
    return {"logit": math.log(p_model / (1.0 - p_model))}


def compute_sigmoid_probability(inputs: dict[str, Any]) -> dict[str, float]:
    logit = _num(inputs, "logit")
    return {"sigmoid_probability": 1.0 / (1.0 + math.exp(-logit))}


def compute_probability_calibration_error(inputs: dict[str, Any]) -> dict[str, float]:
    return {"probability_calibration_error": _num(inputs, "observed_frequency") - _num(inputs, "predicted_probability")}


def compute_binary_entropy(inputs: dict[str, Any]) -> dict[str, float]:
    p_value = clamp(_num(inputs, "probability"), EPSILON, 1.0 - EPSILON)
    return {"binary_entropy": -(p_value * math.log(p_value) + (1.0 - p_value) * math.log(1.0 - p_value))}


def compute_ensemble_probability_mean(inputs: dict[str, Any]) -> dict[str, float]:
    return {"ensemble_probability_mean": _mean(_seq(inputs, "probabilities"))}


def compute_weighted_signal_score(inputs: dict[str, Any]) -> dict[str, float]:
    signals = _seq(inputs, "signals")
    weights = _seq(inputs, "weights")
    return {"weighted_signal_score": sum(s * w for s, w in zip(signals, weights, strict=True)) / max(sum(weights), EPSILON)}


def compute_covariance_penalty(inputs: dict[str, Any]) -> dict[str, float]:
    weights = _seq(inputs, "weights")
    covariance = inputs["covariance"]
    total = 0.0
    for i, weight_i in enumerate(weights):
        for j, weight_j in enumerate(weights):
            total += weight_i * float(covariance[i][j]) * weight_j
    return {"covariance_penalty": total * _num(inputs, "lambda_risk")}


def compute_budget_penalty(inputs: dict[str, Any]) -> dict[str, float]:
    costs = _seq(inputs, "costs")
    selections = _seq(inputs, "selections")
    selected_cost = sum(cost * selected for cost, selected in zip(costs, selections, strict=True))
    return {"budget_penalty": _num(inputs, "lambda_budget") * (selected_cost - _num(inputs, "budget")) ** 2}


def compute_exposure_penalty(inputs: dict[str, Any]) -> dict[str, float]:
    exposures = _seq(inputs, "exposures")
    selections = _seq(inputs, "selections")
    selected_exposure = sum(exposure * selected for exposure, selected in zip(exposures, selections, strict=True))
    return {"exposure_penalty": _num(inputs, "lambda_exposure") * (selected_exposure - _num(inputs, "max_exposure")) ** 2}


def compute_one_hot_penalty(inputs: dict[str, Any]) -> dict[str, float]:
    return {"one_hot_penalty": _num(inputs, "lambda_onehot") * (sum(_seq(inputs, "selections")) - 1.0) ** 2}


def compute_incompatibility_penalty(inputs: dict[str, Any]) -> dict[str, float]:
    selections = _seq(inputs, "selections")
    matrix = inputs["incompatibility"]
    total = 0.0
    for i, selected_i in enumerate(selections):
        for j, selected_j in enumerate(selections):
            total += selected_i * float(matrix[i][j]) * selected_j
    return {"incompatibility_penalty": _num(inputs, "lambda_incompat") * total}


def compute_stack_score(inputs: dict[str, Any]) -> dict[str, float]:
    return {
        "stack_score": _num(inputs, "compatibility_score")
        + _num(inputs, "replay_value_score")
        - _num(inputs, "risk_score")
        - _num(inputs, "complexity_score")
    }


def compute_route_readiness_score(inputs: dict[str, Any]) -> dict[str, float]:
    return {
        "route_readiness_score": _num(inputs, "qku_route_score")
        + _num(inputs, "agent_route_score")
        + _num(inputs, "replay_route_score")
        + _num(inputs, "paper_route_score")
        - _num(inputs, "missing_route_penalty")
    }


def compute_materialization_priority_score(inputs: dict[str, Any]) -> dict[str, float]:
    value = (
        _num(inputs, "stage1_trading_relevance_score")
        + _num(inputs, "replay_paper_value_score")
        + _num(inputs, "quantum_priority_score")
        + _num(inputs, "downstream_unlock_score")
        + _num(inputs, "ease_of_materialization_score")
        - _num(inputs, "critical_missing_field_score")
    ) / 6.0
    return {"overall_materialization_priority_score": value}


def compute_data_missing_penalty(inputs: dict[str, Any]) -> dict[str, float]:
    return {"data_missing_penalty": _num(inputs, "missing_required_fields") * _num(inputs, "missing_field_penalty_weight")}


def compute_stability_score(inputs: dict[str, Any]) -> dict[str, float]:
    return {"stability_score": 1.0 / (1.0 + _num(inputs, "rolling_volatility") + _num(inputs, "calibration_error_abs"))}


def compute_cross_market_generalization_score(inputs: dict[str, Any]) -> dict[str, float]:
    return {
        "cross_market_generalization_score": _num(inputs, "venue_coverage_score")
        * _num(inputs, "family_reuse_score")
        * _num(inputs, "input_schema_portability_score")
    }


def compute_quantum_priority_boost(inputs: dict[str, Any]) -> dict[str, float]:
    return {
        "quantum_priority_boost": _num(inputs, "qubo_compatible_flag")
        * _num(inputs, "binary_decision_density_score")
        * _num(inputs, "batch_optimizer_fit_score")
    }


@dataclass(frozen=True)
class FormulaSpec:
    formula_id: str
    expression: str
    compute: FormulaCallable
    required_inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    units_or_type_hints: dict[str, str]
    domain_family_key: str
    subfamily_key: str
    variant_key: str
    test_inputs: dict[str, Any]
    compute_tier: str = "TIER_1_SIMPLE_ARITHMETIC_FORMULA"
    latency_class: str = "HOT_PATH_ELIGIBLE_CANDIDATE"
    tolerance: float = 1.0e-9
    source_truth_status: str = "OWNER_TEMPLATE"
    candidate_truth_status: str = "CANDIDATE"
    replay_paper_candidate_flag: bool = True

    @property
    def callable_ref(self) -> str:
        return f"{__name__}:{self.compute.__name__}"

    def test_vector(self) -> dict[str, Any]:
        return {
            "test_vector_id": f"PR162D_R2A_TV_FORMULA::{self.formula_id}",
            "callable_ref": self.callable_ref,
            "inputs": self.test_inputs,
            "expected_outputs": self.compute(dict(self.test_inputs)),
            "tolerance": self.tolerance,
            "source_truth_status": self.source_truth_status,
            "candidate_truth_status": self.candidate_truth_status,
            "live_order_authority": False,
        }


def formula_specs() -> list[FormulaSpec]:
    specs = [
        FormulaSpec("YES_EV", "yes_ev = p_model * payout - yes_price - fee_estimate - slippage_estimate - latency_cost_estimate", compute_yes_ev, ("p_model", "payout", "yes_price", "fee_estimate", "slippage_estimate", "latency_cost_estimate"), ("yes_ev",), {"yes_ev": "currency_or_probability_points"}, "expected_value_probability_edge", "yes_ev", "owner_template_v1", {"p_model": 0.62, "payout": 1.0, "yes_price": 0.51, "fee_estimate": 0.01, "slippage_estimate": 0.02, "latency_cost_estimate": 0.005}),
        FormulaSpec("NO_EV", "no_ev = (1 - p_model) * payout - no_price - fee_estimate - slippage_estimate - latency_cost_estimate", compute_no_ev, ("p_model", "payout", "no_price", "fee_estimate", "slippage_estimate", "latency_cost_estimate"), ("no_ev",), {"no_ev": "currency_or_probability_points"}, "expected_value_probability_edge", "no_ev", "owner_template_v1", {"p_model": 0.62, "payout": 1.0, "no_price": 0.37, "fee_estimate": 0.01, "slippage_estimate": 0.02, "latency_cost_estimate": 0.005}),
        FormulaSpec("IMPLIED_PROBABILITY", "implied_probability = clamp(price / max(payout, epsilon), 0, 1)", compute_implied_probability, ("price", "payout"), ("implied_probability",), {"implied_probability": "probability"}, "expected_value_probability_edge", "implied_probability", "owner_template_v1", {"price": 0.43, "payout": 1.0}),
        FormulaSpec("PROBABILITY_EDGE", "probability_edge = p_model - implied_probability", compute_probability_edge, ("p_model", "implied_probability"), ("probability_edge",), {"probability_edge": "probability_delta"}, "expected_value_probability_edge", "probability_edge", "owner_template_v1", {"p_model": 0.58, "implied_probability": 0.52}),
        FormulaSpec("NET_EDGE", "net_edge = expected_net_value / max(entry_price, epsilon)", compute_net_edge, ("expected_net_value", "entry_price"), ("net_edge",), {"net_edge": "ratio"}, "expected_value_probability_edge", "net_edge", "owner_template_v1", {"expected_net_value": 0.04, "entry_price": 0.5}),
        FormulaSpec("MID_PRICE", "mid_price = (best_bid + best_ask) / 2", compute_mid_price, ("best_bid", "best_ask"), ("mid_price",), {"mid_price": "price"}, "market_microstructure_liquidity", "mid_price", "owner_template_v1", {"best_bid": 0.42, "best_ask": 0.46}),
        FormulaSpec("SPREAD", "spread = best_ask - best_bid", compute_spread, ("best_bid", "best_ask"), ("spread",), {"spread": "price_delta"}, "market_microstructure_liquidity", "spread", "owner_template_v1", {"best_bid": 0.42, "best_ask": 0.46}),
        FormulaSpec("RELATIVE_SPREAD", "relative_spread = spread / max(mid_price, epsilon)", compute_relative_spread, ("spread", "mid_price"), ("relative_spread",), {"relative_spread": "ratio"}, "market_microstructure_liquidity", "relative_spread", "owner_template_v1", {"spread": 0.04, "mid_price": 0.44}),
        FormulaSpec("ORDERBOOK_IMBALANCE", "orderbook_imbalance = (bid_size - ask_size) / max(bid_size + ask_size, epsilon)", compute_orderbook_imbalance, ("bid_size", "ask_size"), ("orderbook_imbalance",), {"orderbook_imbalance": "ratio"}, "market_microstructure_liquidity", "orderbook_imbalance", "owner_template_v1", {"bid_size": 120.0, "ask_size": 80.0}),
        FormulaSpec("LIQUIDITY_SCORE", "liquidity_score = log1p(volume) * log1p(depth) / max(spread, tick_size_or_epsilon)", compute_liquidity_score, ("volume", "depth", "spread", "tick_size_or_epsilon"), ("liquidity_score",), {"liquidity_score": "unitless_score"}, "market_microstructure_liquidity", "liquidity_score", "owner_template_v1", {"volume": 1000.0, "depth": 450.0, "spread": 0.03, "tick_size_or_epsilon": 0.01}),
        FormulaSpec("LATENCY_COST", "latency_cost = abs(price_velocity_per_second) * expected_latency_seconds * notional_sensitivity", compute_latency_cost, ("price_velocity_per_second", "expected_latency_seconds", "notional_sensitivity"), ("latency_cost",), {"latency_cost": "price_or_currency_delta"}, "latency_slippage_cost", "latency_cost", "owner_template_v1", {"price_velocity_per_second": -0.02, "expected_latency_seconds": 2.5, "notional_sensitivity": 100.0}),
        FormulaSpec("SLIPPAGE_ESTIMATE", "slippage_estimate = spread_component + depth_impact_component + volatility_impact_component", compute_slippage_estimate, ("spread_component", "depth_impact_component", "volatility_impact_component"), ("slippage_estimate",), {"slippage_estimate": "price_or_currency_delta"}, "latency_slippage_cost", "slippage_estimate", "owner_template_v1", {"spread_component": 0.01, "depth_impact_component": 0.015, "volatility_impact_component": 0.02}),
        FormulaSpec("KELLY_CAPPED", "kelly_capped = clamp(((edge_probability * odds_payoff_ratio - loss_probability) / max(odds_payoff_ratio, epsilon)), 0, max_fraction_cap)", compute_kelly_capped, ("edge_probability", "odds_payoff_ratio", "loss_probability", "max_fraction_cap"), ("kelly_raw", "kelly_capped"), {"kelly_capped": "capital_fraction"}, "risk_capital_sizing", "kelly", "capped_owner_template_v1", {"edge_probability": 0.57, "odds_payoff_ratio": 1.2, "loss_probability": 0.43, "max_fraction_cap": 0.1}),
        FormulaSpec("BRIER_SCORE", "brier_score = mean((actual_outcome - predicted_probability)^2)", compute_brier_score, ("actual_outcomes", "predicted_probabilities"), ("brier_score",), {"brier_score": "loss"}, "probability_calibration_edge", "brier_score", "owner_template_v1", {"actual_outcomes": [0, 1, 1, 0], "predicted_probabilities": [0.1, 0.9, 0.8, 0.3]}),
        FormulaSpec("LOG_LOSS", "log_loss = -mean(y * log(p_clipped) + (1 - y) * log(1 - p_clipped))", compute_log_loss, ("actual_outcomes", "predicted_probabilities"), ("log_loss",), {"log_loss": "loss"}, "probability_calibration_edge", "log_loss", "owner_template_v1", {"actual_outcomes": [0, 1, 1, 0], "predicted_probabilities": [0.1, 0.9, 0.8, 0.3]}),
        FormulaSpec("EMA", "ema_t = alpha * price_t + (1 - alpha) * ema_t_minus_1", compute_ema, ("alpha", "price_t", "ema_t_minus_1"), ("ema_t",), {"ema_t": "price"}, "technical_indicator_price_feature", "EMA", "owner_template_v1", {"alpha": 0.2, "price_t": 0.55, "ema_t_minus_1": 0.5}, "TIER_2_VECTORIZED_FEATURE_FORMULA", "INCREMENTAL_UPDATE_ELIGIBLE"),
        FormulaSpec("SIMPLE_RETURN", "simple_return = price_t / max(price_t_minus_1, epsilon) - 1", compute_simple_return, ("price_t", "price_t_minus_1"), ("simple_return",), {"simple_return": "return_ratio"}, "technical_indicator_price_feature", "returns", "simple_owner_template_v1", {"price_t": 0.55, "price_t_minus_1": 0.5}),
        FormulaSpec("ROLLING_VOLATILITY", "rolling_volatility = std(returns_window)", compute_rolling_volatility, ("returns_window",), ("rolling_volatility",), {"rolling_volatility": "return_std"}, "technical_indicator_price_feature", "volatility", "rolling_owner_template_v1", {"returns_window": [0.02, -0.01, 0.03, 0.0]}, "TIER_2_VECTORIZED_FEATURE_FORMULA", "PRECOMPUTE_REQUIRED"),
        FormulaSpec("VWAP", "vwap = sum(price_i * volume_i) / max(sum(volume_i), epsilon)", compute_vwap, ("prices", "volumes"), ("vwap",), {"vwap": "price"}, "technical_indicator_price_feature", "VWAP", "owner_template_v1", {"prices": [0.4, 0.5, 0.6], "volumes": [100, 200, 100]}, "TIER_2_VECTORIZED_FEATURE_FORMULA", "PRECOMPUTE_REQUIRED"),
        FormulaSpec("BOLLINGER_Z", "bollinger_z = (price - rolling_mean) / max(rolling_std, epsilon)", compute_bollinger_z, ("price", "rolling_mean", "rolling_std"), ("bollinger_z",), {"bollinger_z": "z_score"}, "technical_indicator_price_feature", "Bollinger", "z_score_owner_template_v1", {"price": 0.58, "rolling_mean": 0.5, "rolling_std": 0.04}),
        FormulaSpec("RSI", "rsi = 100 - 100 / (1 + mean(max(delta_i,0)) / max(mean(abs(min(delta_i,0))), epsilon))", compute_rsi, ("deltas",), ("avg_gain", "avg_loss", "rs", "rsi"), {"rsi": "index_0_to_100"}, "technical_indicator_price_feature", "RSI", "owner_template_v1", {"deltas": [0.02, -0.01, 0.03, -0.02, 0.01]}, "TIER_2_VECTORIZED_FEATURE_FORMULA", "PRECOMPUTE_REQUIRED"),
        FormulaSpec("MACD", "macd = ema_fast - ema_slow; macd_signal = ema(macd, signal_alpha); macd_histogram = macd - macd_signal", compute_macd, ("ema_fast", "ema_slow", "signal_alpha", "macd_signal_t_minus_1"), ("macd", "macd_signal", "macd_histogram"), {"macd": "price_delta"}, "technical_indicator_price_feature", "MACD", "owner_template_v1", {"ema_fast": 0.55, "ema_slow": 0.5, "signal_alpha": 0.2, "macd_signal_t_minus_1": 0.02}, "TIER_2_VECTORIZED_FEATURE_FORMULA", "PRECOMPUTE_REQUIRED"),
        FormulaSpec("RISK_ADJUSTED_SCORE", "risk_adjusted_score = expected_net_value - drawdown_penalty_lambda*drawdown_risk - latency_penalty_lambda*latency_cost - slippage_penalty_lambda*slippage_estimate - complexity_penalty_lambda*complexity_score", compute_risk_adjusted_score, ("expected_net_value", "drawdown_penalty_lambda", "drawdown_risk", "latency_penalty_lambda", "latency_cost", "slippage_penalty_lambda", "slippage_estimate", "complexity_penalty_lambda", "complexity_score"), ("risk_adjusted_score",), {"risk_adjusted_score": "score"}, "risk_capital_sizing", "risk_adjusted_score", "owner_template_v1", {"expected_net_value": 0.08, "drawdown_penalty_lambda": 0.5, "drawdown_risk": 0.02, "latency_penalty_lambda": 0.1, "latency_cost": 0.01, "slippage_penalty_lambda": 0.2, "slippage_estimate": 0.015, "complexity_penalty_lambda": 0.1, "complexity_score": 0.2}),
        FormulaSpec("CANDIDATE_SELECTION_SCORE", "candidate_selection_score = replay_value_score + paper_value_score + stability_score + cross_market_generalization_score + quantum_priority_boost - latency_penalty - drawdown_penalty - data_missing_penalty - complexity_penalty", compute_candidate_selection_score, ("replay_value_score", "paper_value_score", "stability_score", "cross_market_generalization_score", "quantum_priority_boost", "latency_penalty", "drawdown_penalty", "data_missing_penalty", "complexity_penalty"), ("candidate_selection_score",), {"candidate_selection_score": "score"}, "deterministic_candidate_ranking_algorithm", "candidate_selection_score", "owner_template_v1", {"replay_value_score": 0.8, "paper_value_score": 0.7, "stability_score": 0.6, "cross_market_generalization_score": 0.5, "quantum_priority_boost": 0.2, "latency_penalty": 0.1, "drawdown_penalty": 0.05, "data_missing_penalty": 0.0, "complexity_penalty": 0.1}),
    ]
    extras = [
        ("DEPTH_IMPACT_COMPONENT", "depth_impact_component = order_size / max(available_depth, epsilon)", compute_depth_impact_component, ("order_size", "available_depth"), ("depth_impact_component",), "latency_slippage_cost", "slippage_depth", {"order_size": 50, "available_depth": 500}),
        ("VOLATILITY_IMPACT_COMPONENT", "volatility_impact_component = rolling_volatility * sqrt(holding_period_seconds)", compute_volatility_impact_component, ("rolling_volatility", "holding_period_seconds"), ("volatility_impact_component",), "latency_slippage_cost", "slippage_volatility", {"rolling_volatility": 0.02, "holding_period_seconds": 9}),
        ("SPREAD_COMPONENT", "spread_component = spread * spread_capture_fraction", compute_spread_component, ("spread", "spread_capture_fraction"), ("spread_component",), "latency_slippage_cost", "spread_component", {"spread": 0.04, "spread_capture_fraction": 0.5}),
        ("DEPTH_WEIGHTED_MID_PRICE", "depth_weighted_mid_price = (best_bid*ask_size + best_ask*bid_size) / max(bid_size + ask_size, epsilon)", compute_depth_weighted_mid_price, ("best_bid", "best_ask", "bid_size", "ask_size"), ("depth_weighted_mid_price",), "market_microstructure_liquidity", "depth_weighted_mid", {"best_bid": 0.42, "best_ask": 0.46, "bid_size": 100, "ask_size": 50}),
        ("TOP_OF_BOOK_DEPTH", "top_of_book_depth = bid_size + ask_size", compute_top_of_book_depth, ("bid_size", "ask_size"), ("top_of_book_depth",), "market_microstructure_liquidity", "top_of_book_depth", {"bid_size": 100, "ask_size": 50}),
        ("MARKET_PRESSURE", "market_pressure = orderbook_imbalance * relative_spread", compute_market_pressure, ("orderbook_imbalance", "relative_spread"), ("market_pressure",), "market_microstructure_liquidity", "market_pressure", {"orderbook_imbalance": 0.2, "relative_spread": 0.05}),
        ("VOLUME_GROWTH_RATE", "volume_growth_rate = volume_t / max(volume_t_minus_1, epsilon) - 1", compute_volume_growth_rate, ("volume_t", "volume_t_minus_1"), ("volume_growth_rate",), "technical_indicator_price_feature", "volume", {"volume_t": 1500, "volume_t_minus_1": 1000}),
        ("CANDLE_RETURN", "candle_return = close_price / max(open_price, epsilon) - 1", compute_candle_return, ("close_price", "open_price"), ("candle_return",), "technical_indicator_price_feature", "returns", {"close_price": 0.55, "open_price": 0.5}),
        ("HIGH_LOW_RANGE", "high_low_range = high_price - low_price", compute_high_low_range, ("high_price", "low_price"), ("high_low_range",), "technical_indicator_price_feature", "candlestick", {"high_price": 0.6, "low_price": 0.45}),
        ("CANDLE_BODY", "candle_body = abs(close_price - open_price)", compute_candle_body, ("close_price", "open_price"), ("candle_body",), "technical_indicator_price_feature", "candlestick", {"close_price": 0.55, "open_price": 0.5}),
        ("WICK_RATIO", "wick_ratio = ((high_price - low_price) - abs(close_price - open_price)) / max(high_price - low_price, epsilon)", compute_wick_ratio, ("high_price", "low_price", "close_price", "open_price"), ("wick_ratio",), "technical_indicator_price_feature", "candlestick", {"high_price": 0.62, "low_price": 0.42, "close_price": 0.55, "open_price": 0.5}),
        ("REALIZED_SPREAD_PROXY", "realized_spread_proxy = abs(execution_price - mid_price_after_delay)", compute_realized_spread_proxy, ("execution_price", "mid_price_after_delay"), ("realized_spread_proxy",), "market_microstructure_liquidity", "realized_spread", {"execution_price": 0.51, "mid_price_after_delay": 0.49}),
        ("MOMENTUM_N_PERIOD", "momentum_n_period = price_t - price_t_minus_n", compute_momentum_n_period, ("price_t", "price_t_minus_n"), ("momentum_n_period",), "technical_indicator_price_feature", "momentum", {"price_t": 0.57, "price_t_minus_n": 0.5}),
        ("PRICE_ZSCORE", "price_zscore = (price - mean_price) / max(std_price, epsilon)", compute_price_zscore, ("price", "mean_price", "std_price"), ("price_zscore",), "technical_indicator_price_feature", "zscore", {"price": 0.57, "mean_price": 0.5, "std_price": 0.035}),
        ("SHARPE_LIKE_SCORE", "sharpe_like_score = mean_return / max(return_volatility, epsilon)", compute_sharpe_like_score, ("mean_return", "return_volatility"), ("sharpe_like_score",), "risk_capital_sizing", "risk_return", {"mean_return": 0.03, "return_volatility": 0.02}),
        ("EXPECTED_SHORTFALL_PROXY", "expected_shortfall_proxy = mean(losses >= var_threshold)", compute_expected_shortfall_proxy, ("losses", "var_threshold"), ("expected_shortfall_proxy",), "risk_capital_sizing", "expected_shortfall", {"losses": [0.01, 0.04, 0.08, 0.02], "var_threshold": 0.03}),
        ("CAPITAL_UTILIZATION", "capital_utilization = capital_used / max(capital_budget, epsilon)", compute_capital_utilization, ("capital_used", "capital_budget"), ("capital_utilization",), "risk_capital_sizing", "capital_utilization", {"capital_used": 250, "capital_budget": 1000}),
        ("EXPOSURE_UTILIZATION", "exposure_utilization = exposure_used / max(max_exposure, epsilon)", compute_exposure_utilization, ("exposure_used", "max_exposure"), ("exposure_utilization",), "risk_capital_sizing", "exposure_utilization", {"exposure_used": 300, "max_exposure": 1000}),
        ("COST_TO_BUDGET_RATIO", "cost_to_budget_ratio = candidate_cost / max(budget, epsilon)", compute_cost_to_budget_ratio, ("candidate_cost", "budget"), ("cost_to_budget_ratio",), "risk_capital_sizing", "budget_ratio", {"candidate_cost": 75, "budget": 500}),
        ("LOGIT", "logit = log(p_model / (1 - p_model))", compute_logit, ("p_model",), ("logit",), "probability_calibration_edge", "logit", {"p_model": 0.6}),
        ("SIGMOID_PROBABILITY", "sigmoid_probability = 1 / (1 + exp(-logit))", compute_sigmoid_probability, ("logit",), ("sigmoid_probability",), "probability_calibration_edge", "sigmoid", {"logit": 0.4}),
        ("PROBABILITY_CALIBRATION_ERROR", "probability_calibration_error = observed_frequency - predicted_probability", compute_probability_calibration_error, ("observed_frequency", "predicted_probability"), ("probability_calibration_error",), "probability_calibration_edge", "calibration_error", {"observed_frequency": 0.55, "predicted_probability": 0.5}),
        ("BINARY_ENTROPY", "binary_entropy = -(p*log(p) + (1-p)*log(1-p))", compute_binary_entropy, ("probability",), ("binary_entropy",), "probability_calibration_edge", "entropy", {"probability": 0.5}),
        ("ENSEMBLE_PROBABILITY_MEAN", "ensemble_probability_mean = mean(probabilities)", compute_ensemble_probability_mean, ("probabilities",), ("ensemble_probability_mean",), "probability_calibration_edge", "ensemble", {"probabilities": [0.5, 0.6, 0.55]}),
        ("WEIGHTED_SIGNAL_SCORE", "weighted_signal_score = sum(signal_i*weight_i)/max(sum(weights), epsilon)", compute_weighted_signal_score, ("signals", "weights"), ("weighted_signal_score",), "deterministic_candidate_ranking_algorithm", "weighted_signal", {"signals": [0.2, 0.6, 0.8], "weights": [1, 2, 1]}),
        ("COVARIANCE_PENALTY", "covariance_penalty = lambda_risk * w^T covariance w", compute_covariance_penalty, ("weights", "covariance", "lambda_risk"), ("covariance_penalty",), "quantum_bundle_selection_optimizer", "risk_penalty", {"weights": [1, 0], "covariance": [[0.1, 0.02], [0.02, 0.2]], "lambda_risk": 0.5}),
        ("BUDGET_PENALTY", "budget_penalty = lambda_budget * (sum(cost_i*x_i) - budget)^2", compute_budget_penalty, ("costs", "selections", "budget", "lambda_budget"), ("budget_penalty",), "quantum_bundle_selection_optimizer", "budget_penalty", {"costs": [20, 30], "selections": [1, 1], "budget": 40, "lambda_budget": 0.1}),
        ("EXPOSURE_PENALTY", "exposure_penalty = lambda_exposure * (sum(exposure_i*x_i) - max_exposure)^2", compute_exposure_penalty, ("exposures", "selections", "max_exposure", "lambda_exposure"), ("exposure_penalty",), "quantum_bundle_selection_optimizer", "exposure_penalty", {"exposures": [10, 20], "selections": [1, 1], "max_exposure": 25, "lambda_exposure": 0.1}),
        ("ONE_HOT_PENALTY", "one_hot_penalty = lambda_onehot * (sum(x_i) - 1)^2", compute_one_hot_penalty, ("selections", "lambda_onehot"), ("one_hot_penalty",), "quantum_bundle_selection_optimizer", "one_hot_penalty", {"selections": [1, 0, 0], "lambda_onehot": 2.0}),
        ("INCOMPATIBILITY_PENALTY", "incompatibility_penalty = lambda_incompat * sum(incompatibility_ij*x_i*x_j)", compute_incompatibility_penalty, ("selections", "incompatibility", "lambda_incompat"), ("incompatibility_penalty",), "quantum_bundle_selection_optimizer", "incompatibility_penalty", {"selections": [1, 1], "incompatibility": [[0, 1], [1, 0]], "lambda_incompat": 0.5}),
        ("STACK_SCORE", "stack_score = compatibility_score + replay_value_score - risk_score - complexity_score", compute_stack_score, ("compatibility_score", "replay_value_score", "risk_score", "complexity_score"), ("stack_score",), "parameter_default_range_pack", "optimizer_parameters", {"compatibility_score": 0.8, "replay_value_score": 0.6, "risk_score": 0.2, "complexity_score": 0.1}),
        ("ROUTE_READINESS_SCORE", "route_readiness_score = qku_route_score + agent_route_score + replay_route_score + paper_route_score - missing_route_penalty", compute_route_readiness_score, ("qku_route_score", "agent_route_score", "replay_route_score", "paper_route_score", "missing_route_penalty"), ("route_readiness_score",), "deterministic_candidate_ranking_algorithm", "route_readiness", {"qku_route_score": 1, "agent_route_score": 1, "replay_route_score": 1, "paper_route_score": 1, "missing_route_penalty": 0}),
        ("MATERIALIZATION_PRIORITY_SCORE", "overall_materialization_priority_score = weighted materialization priority components", compute_materialization_priority_score, ("stage1_trading_relevance_score", "replay_paper_value_score", "quantum_priority_score", "downstream_unlock_score", "ease_of_materialization_score", "critical_missing_field_score"), ("overall_materialization_priority_score",), "deterministic_candidate_ranking_algorithm", "materialization_priority", {"stage1_trading_relevance_score": 0.9, "replay_paper_value_score": 0.8, "quantum_priority_score": 0.4, "downstream_unlock_score": 0.7, "ease_of_materialization_score": 0.9, "critical_missing_field_score": 0.1}),
        ("DATA_MISSING_PENALTY", "data_missing_penalty = missing_required_fields * missing_field_penalty_weight", compute_data_missing_penalty, ("missing_required_fields", "missing_field_penalty_weight"), ("data_missing_penalty",), "deterministic_candidate_ranking_algorithm", "data_missing_penalty", {"missing_required_fields": 2, "missing_field_penalty_weight": 0.15}),
        ("STABILITY_SCORE", "stability_score = 1 / (1 + rolling_volatility + abs(calibration_error))", compute_stability_score, ("rolling_volatility", "calibration_error_abs"), ("stability_score",), "probability_calibration_edge", "stability", {"rolling_volatility": 0.02, "calibration_error_abs": 0.05}),
        ("CROSS_MARKET_GENERALIZATION_SCORE", "cross_market_generalization_score = venue_coverage_score * family_reuse_score * input_schema_portability_score", compute_cross_market_generalization_score, ("venue_coverage_score", "family_reuse_score", "input_schema_portability_score"), ("cross_market_generalization_score",), "deterministic_candidate_ranking_algorithm", "generalization", {"venue_coverage_score": 0.8, "family_reuse_score": 0.9, "input_schema_portability_score": 0.7}),
        ("QUANTUM_PRIORITY_BOOST", "quantum_priority_boost = qubo_compatible_flag * binary_decision_density_score * batch_optimizer_fit_score", compute_quantum_priority_boost, ("qubo_compatible_flag", "binary_decision_density_score", "batch_optimizer_fit_score"), ("quantum_priority_boost",), "quantum_bundle_selection_optimizer", "quantum_priority", {"qubo_compatible_flag": 1, "binary_decision_density_score": 0.8, "batch_optimizer_fit_score": 0.9}),
    ]
    for formula_id, expression, function, inputs, outputs, family, subfamily, sample in extras:
        specs.append(
            FormulaSpec(
                formula_id,
                expression,
                function,
                tuple(inputs),
                tuple(outputs),
                {output: "numeric" for output in outputs},
                family,
                subfamily,
                "owner_template_v1",
                sample,
                "TIER_2_VECTORIZED_FEATURE_FORMULA" if family == "technical_indicator_price_feature" else "TIER_1_SIMPLE_ARITHMETIC_FORMULA",
                "PRECOMPUTE_REQUIRED" if family in {"technical_indicator_price_feature", "quantum_bundle_selection_optimizer"} else "HOT_PATH_ELIGIBLE_CANDIDATE",
            )
        )
    return specs


def formula_by_id() -> dict[str, FormulaSpec]:
    return {spec.formula_id: spec for spec in formula_specs()}
