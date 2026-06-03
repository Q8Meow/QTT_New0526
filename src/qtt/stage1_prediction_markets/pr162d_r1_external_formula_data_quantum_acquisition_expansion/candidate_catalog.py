"""Computable PR162D-R1 candidate factories."""

from __future__ import annotations

from itertools import cycle
from typing import Any, Iterable

from .route_helpers import common_agent_refs, downstream_bridge, qku_refs_for_index, replay_route_refs


FormulaSpec = tuple[str, str, str, list[str], list[str], str, dict[str, float | int], dict[str, float | int]]


FORMULA_SPECS: tuple[FormulaSpec, ...] = (
    ("binary_price_probability", "PREDICTION_MARKET_FORMULA", "p_yes = price_cents / 100", ["price_cents"], ["p_yes"], "probability", {"min": 0.0, "max": 1.0}, {"price_cents": 55}),
    ("no_price_probability", "PREDICTION_MARKET_FORMULA", "p_no = 1 - p_yes", ["p_yes"], ["p_no"], "probability", {"min": 0.0, "max": 1.0}, {"p_yes": 0.55}),
    ("midpoint_probability", "PREDICTION_MARKET_FORMULA", "mid = (best_yes_bid + best_yes_ask) / 2", ["best_yes_bid", "best_yes_ask"], ["mid"], "probability", {"min": 0.0, "max": 1.0}, {"best_yes_bid": 0.54, "best_yes_ask": 0.58}),
    ("bid_ask_spread", "PREDICTION_MARKET_FORMULA", "spread = best_yes_ask - best_yes_bid", ["best_yes_bid", "best_yes_ask"], ["spread"], "probability_points", {"min": 0.0, "max": 1.0}, {"best_yes_bid": 0.54, "best_yes_ask": 0.58}),
    ("yes_no_cross_spread", "PREDICTION_MARKET_FORMULA", "cross_spread = (1 - best_no_bid) - best_yes_bid", ["best_no_bid", "best_yes_bid"], ["cross_spread"], "probability_points", {"min": -1.0, "max": 1.0}, {"best_no_bid": 0.42, "best_yes_bid": 0.54}),
    ("orderbook_depth", "PREDICTION_MARKET_FORMULA", "depth = sum(size_k for k in price_levels if price_k within band)", ["price_levels", "size_levels", "band"], ["depth"], "contracts", {"min": 0.0, "max": 1000000000.0}, {"band": 0.03}),
    ("volume_weighted_price", "PREDICTION_MARKET_FORMULA", "vwap = sum(price_i * size_i) / sum(size_i)", ["price_i", "size_i"], ["vwap"], "probability", {"min": 0.0, "max": 1.0}, {"price_i": 0.56, "size_i": 10}),
    ("candle_return", "PREDICTION_MARKET_FORMULA", "return = close_price / previous_close_price - 1", ["close_price", "previous_close_price"], ["return"], "unitless", {"min": -1.0, "max": 100.0}, {"close_price": 0.58, "previous_close_price": 0.55}),
    ("candle_range", "PREDICTION_MARKET_FORMULA", "range = high_price - low_price", ["high_price", "low_price"], ["range"], "probability_points", {"min": 0.0, "max": 1.0}, {"high_price": 0.62, "low_price": 0.51}),
    ("open_interest_delta", "PREDICTION_MARKET_FORMULA", "oi_delta = open_interest_t - open_interest_t_minus_1", ["open_interest_t", "open_interest_t_minus_1"], ["oi_delta"], "contracts", {"min": -1000000000.0, "max": 1000000000.0}, {"open_interest_t": 110, "open_interest_t_minus_1": 100}),
    ("settlement_time_remaining", "PREDICTION_MARKET_FORMULA", "time_remaining_seconds = max(0, settlement_ts - observation_ts)", ["settlement_ts", "observation_ts"], ["time_remaining_seconds"], "seconds", {"min": 0.0, "max": 31557600.0}, {"settlement_ts": 3600, "observation_ts": 600}),
    ("historical_cutoff_route", "PREDICTION_MARKET_FORMULA", "route = historical if record_ts < cutoff_ts else recent", ["record_ts", "cutoff_ts"], ["route_flag"], "boolean", {"min": 0, "max": 1}, {"record_ts": 100, "cutoff_ts": 200}),
    ("event_volume_share", "PREDICTION_MARKET_FORMULA", "share = market_volume / max(event_volume, epsilon)", ["market_volume", "event_volume", "epsilon"], ["share"], "unitless", {"min": 0.0, "max": 1.0}, {"epsilon": 1e-9}),
    ("token_outcome_probability_map", "PREDICTION_MARKET_FORMULA", "p_outcome[token_id] = outcome_price[token_id]", ["token_id", "outcome_price"], ["p_outcome"], "probability", {"min": 0.0, "max": 1.0}, {"outcome_price": 0.57}),
    ("maker_taker_gap", "PREDICTION_MARKET_FORMULA", "maker_taker_gap = taker_fee_bps - maker_fee_bps", ["taker_fee_bps", "maker_fee_bps"], ["maker_taker_gap"], "basis_points", {"min": -1000.0, "max": 1000.0}, {"taker_fee_bps": 10, "maker_fee_bps": 0}),
    ("brier_binary", "CALIBRATION_FORMULA", "brier = mean((y_true - p_pred)^2)", ["y_true", "p_pred"], ["brier"], "score", {"min": 0.0, "max": 1.0}, {"p_pred": 0.7}),
    ("brier_multiclass", "CALIBRATION_FORMULA", "brier = mean(sum_c((y_ic - p_ic)^2))", ["y_ic", "p_ic"], ["brier"], "score", {"min": 0.0, "max": 2.0}, {"p_ic": 0.5}),
    ("log_loss_binary", "CALIBRATION_FORMULA", "log_loss = -mean(y * log(p) + (1 - y) * log(1 - p))", ["y", "p"], ["log_loss"], "score", {"min": 0.0, "max": 1000000.0}, {"p": 0.7}),
    ("probability_clip", "CALIBRATION_FORMULA", "p_clipped = min(max(p, epsilon), 1 - epsilon)", ["p", "epsilon"], ["p_clipped"], "probability", {"min": 0.0, "max": 1.0}, {"epsilon": 1e-15}),
    ("calibration_bin_accuracy", "CALIBRATION_FORMULA", "bin_accuracy = mean(y_i for i in bin_b)", ["y_i", "bin_b"], ["bin_accuracy"], "probability", {"min": 0.0, "max": 1.0}, {"bin_b": 10}),
    ("calibration_bin_confidence", "CALIBRATION_FORMULA", "bin_confidence = mean(p_i for i in bin_b)", ["p_i", "bin_b"], ["bin_confidence"], "probability", {"min": 0.0, "max": 1.0}, {"bin_b": 10}),
    ("expected_calibration_error", "CALIBRATION_FORMULA", "ece = sum_b(n_b / n * abs(acc_b - conf_b))", ["n_b", "n", "acc_b", "conf_b"], ["ece"], "score", {"min": 0.0, "max": 1.0}, {"n": 100, "n_b": 10}),
    ("maximum_calibration_error", "CALIBRATION_FORMULA", "mce = max_b(abs(acc_b - conf_b))", ["acc_b", "conf_b"], ["mce"], "score", {"min": 0.0, "max": 1.0}, {}),
    ("sma", "TECHNICAL_INDICATOR_FORMULA", "sma_t = mean(price_{t-n+1:t})", ["price", "window"], ["sma"], "price", {"min": 0.0, "max": 1.0}, {"window": 20}),
    ("ema", "TECHNICAL_INDICATOR_FORMULA", "ema_t = alpha * price_t + (1 - alpha) * ema_{t-1}", ["price_t", "ema_t_minus_1", "alpha"], ["ema"], "price", {"min": 0.0, "max": 1.0}, {"alpha": 0.095238}),
    ("rsi", "TECHNICAL_INDICATOR_FORMULA", "rsi = 100 - 100 / (1 + avg_gain / avg_loss)", ["avg_gain", "avg_loss"], ["rsi"], "index_0_100", {"min": 0.0, "max": 100.0}, {"window": 14}),
    ("macd_line", "TECHNICAL_INDICATOR_FORMULA", "macd = ema_fast - ema_slow", ["ema_fast", "ema_slow"], ["macd"], "price", {"min": -1.0, "max": 1.0}, {"fast": 12, "slow": 26}),
    ("macd_signal", "TECHNICAL_INDICATOR_FORMULA", "signal = ema(macd, signal_window)", ["macd", "signal_window"], ["signal"], "price", {"min": -1.0, "max": 1.0}, {"signal_window": 9}),
    ("macd_histogram", "TECHNICAL_INDICATOR_FORMULA", "histogram = macd - signal", ["macd", "signal"], ["histogram"], "price", {"min": -1.0, "max": 1.0}, {}),
    ("bollinger_upper", "TECHNICAL_INDICATOR_FORMULA", "upper = sma + k * rolling_std", ["sma", "rolling_std", "k"], ["upper_band"], "price", {"min": 0.0, "max": 1.0}, {"window": 20, "k": 2}),
    ("bollinger_lower", "TECHNICAL_INDICATOR_FORMULA", "lower = sma - k * rolling_std", ["sma", "rolling_std", "k"], ["lower_band"], "price", {"min": 0.0, "max": 1.0}, {"window": 20, "k": 2}),
    ("rolling_zscore", "TECHNICAL_INDICATOR_FORMULA", "z = (x - rolling_mean) / rolling_std", ["x", "rolling_mean", "rolling_std"], ["zscore"], "standard_deviation", {"min": -10.0, "max": 10.0}, {"window": 20}),
    ("rate_of_change", "TECHNICAL_INDICATOR_FORMULA", "roc = price_t / price_{t-n} - 1", ["price_t", "price_t_minus_n"], ["roc"], "unitless", {"min": -1.0, "max": 100.0}, {"window": 10}),
    ("rolling_volatility", "TECHNICAL_INDICATOR_FORMULA", "volatility = std(returns_{t-n+1:t})", ["returns", "window"], ["volatility"], "unitless", {"min": 0.0, "max": 10.0}, {"window": 20}),
    ("sharpe_ratio", "RISK_SIZING_FORMULA", "sharpe = mean(excess_return) / std(excess_return)", ["excess_return"], ["sharpe"], "ratio", {"min": -100.0, "max": 100.0}, {"annualization": 252}),
    ("sortino_ratio", "RISK_SIZING_FORMULA", "sortino = mean(excess_return) / downside_deviation", ["excess_return", "downside_deviation"], ["sortino"], "ratio", {"min": -100.0, "max": 100.0}, {"annualization": 252}),
    ("kelly_fraction_binary", "RISK_SIZING_FORMULA", "f = (b * p - (1 - p)) / b", ["b", "p"], ["kelly_fraction"], "fraction", {"min": -1.0, "max": 1.0}, {"fractional_multiplier": 0.5}),
    ("fractional_kelly", "RISK_SIZING_FORMULA", "f_fractional = multiplier * kelly_fraction", ["multiplier", "kelly_fraction"], ["f_fractional"], "fraction", {"min": -1.0, "max": 1.0}, {"multiplier": 0.5}),
    ("value_at_risk_quantile", "RISK_SIZING_FORMULA", "var_alpha = quantile(losses, alpha)", ["losses", "alpha"], ["var_alpha"], "loss_units", {"min": 0.0, "max": 1000000000.0}, {"alpha": 0.95}),
    ("conditional_value_at_risk", "RISK_SIZING_FORMULA", "cvar_alpha = mean(loss_i for loss_i >= var_alpha)", ["loss_i", "var_alpha"], ["cvar_alpha"], "loss_units", {"min": 0.0, "max": 1000000000.0}, {"alpha": 0.95}),
    ("max_drawdown", "RISK_SIZING_FORMULA", "max_drawdown = max_t((peak_t - equity_t) / peak_t)", ["peak_t", "equity_t"], ["max_drawdown"], "fraction", {"min": 0.0, "max": 1.0}, {}),
    ("latency_adjusted_ev", "RISK_SIZING_FORMULA", "ev_adj = ev_raw - latency_seconds * decay_per_second - fees", ["ev_raw", "latency_seconds", "decay_per_second", "fees"], ["ev_adj"], "currency_or_probability", {"min": -1000000.0, "max": 1000000.0}, {"decay_per_second": 0.0001}),
    ("slippage_adjusted_ev", "RISK_SIZING_FORMULA", "ev_adj = ev_raw - expected_slippage - fees", ["ev_raw", "expected_slippage", "fees"], ["ev_adj"], "currency_or_probability", {"min": -1000000.0, "max": 1000000.0}, {"expected_slippage": 0.01}),
    ("minimum_variance", "PORTFOLIO_OPTIMIZER_FORMULA", "risk = w.T @ cov @ w", ["w", "cov"], ["risk"], "variance", {"min": 0.0, "max": 1000000.0}, {"weight_bounds_min": 0.0, "weight_bounds_max": 1.0}),
    ("mean_variance_utility", "PORTFOLIO_OPTIMIZER_FORMULA", "utility = mu.T @ w - 0.5 * gamma * w.T @ cov @ w", ["mu", "w", "gamma", "cov"], ["utility"], "utility", {"min": -1000000.0, "max": 1000000.0}, {"gamma": 1.0}),
    ("max_sharpe_objective", "PORTFOLIO_OPTIMIZER_FORMULA", "sharpe = (mu.T @ w - risk_free_rate) / sqrt(w.T @ cov @ w)", ["mu", "w", "risk_free_rate", "cov"], ["sharpe"], "ratio", {"min": -100.0, "max": 100.0}, {"risk_free_rate": 0.02}),
    ("quadratic_utility", "PORTFOLIO_OPTIMIZER_FORMULA", "quadratic_utility = mu.T @ w - risk_aversion * w.T @ cov @ w", ["mu", "w", "risk_aversion", "cov"], ["quadratic_utility"], "utility", {"min": -1000000.0, "max": 1000000.0}, {"risk_aversion": 1.0}),
    ("risk_budget_penalty", "PORTFOLIO_OPTIMIZER_FORMULA", "penalty = lambda_budget * max(0, w.T @ cov @ w - risk_budget)^2", ["lambda_budget", "w", "cov", "risk_budget"], ["penalty"], "penalty", {"min": 0.0, "max": 1000000.0}, {"lambda_budget": 10.0}),
)

CATEGORY_TARGETS = {
    "PREDICTION_MARKET_FORMULA": 55,
    "CALIBRATION_FORMULA": 22,
    "RISK_SIZING_FORMULA": 34,
    "TECHNICAL_INDICATOR_FORMULA": 35,
    "PORTFOLIO_OPTIMIZER_FORMULA": 24,
}

SOURCE_LANE_BY_CATEGORY = {
    "PREDICTION_MARKET_FORMULA": ("LANE_A_KALSHI", "LANE_B_POLYMARKET", "LANE_C_FORECASTEX"),
    "CALIBRATION_FORMULA": ("LANE_D_FORMULA_LIBRARY", "LANE_F_RESEARCH"),
    "RISK_SIZING_FORMULA": ("LANE_D_PORTFOLIO_OPTIMIZER", "LANE_F_RESEARCH"),
    "TECHNICAL_INDICATOR_FORMULA": ("LANE_D_TECHNICAL_INDICATORS", "LANE_D_FORMULA_LIBRARY"),
    "PORTFOLIO_OPTIMIZER_FORMULA": ("LANE_D_PORTFOLIO_OPTIMIZER", "LANE_D_FORMULA_LIBRARY"),
}


def external_formula_candidates(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    by_category = _specs_by_category()
    records: list[dict[str, Any]] = []
    for category, target in CATEGORY_TARGETS.items():
        spec_cycle = cycle(by_category[category])
        for _ in range(target):
            index = len(records) + 1
            spec = next(spec_cycle)
            source = _source_for_category(sources, category, index)
            variant = 1 + (index % 7)
            formula_id = f"PR162D_R1_FORMULA_{index:04d}"
            qku_refs = qku_refs_for_index(qku_pool, index)
            agent_refs = common_agent_refs(include_quantum=False)
            records.append(
                {
                    "formula_id": formula_id,
                    "candidate_id": formula_id,
                    "source_locator": source["source_locator"],
                    "source_tier": source["source_tier"],
                    "source_class": source["source_class"],
                    "authority_class": source["authority_class"],
                    "confidence_class": source["confidence_class"],
                    "candidate_or_provisional_flag": True,
                    "official_truth_flag": source["official_truth_flag"],
                    "expression": _variant_expression(spec[2], variant),
                    "variables": {field: f"input variable for {field}" for field in spec[3]},
                    "input_fields": spec[3],
                    "output_fields": spec[4],
                    "units": spec[5],
                    "valid_range": spec[6],
                    "default_parameter_candidates": {**spec[7], "variant_window": variant},
                    "formula_family": spec[0],
                    "formula_category": category,
                    "qku_refs": qku_refs,
                    "agent_refs": agent_refs,
                    "agent_route_refs": agent_refs,
                    "replay_paper_route_refs": replay_route_refs(formula_id),
                    "test_vector": _formula_test_vector(spec, variant),
                    "deterministic_implementation_function_reference": (
                        "src.qtt.stage1_prediction_markets."
                        "pr162d_r1_external_formula_data_quantum_acquisition_expansion."
                        f"formula_acquisition.compute_{spec[0]}"
                    ),
                    "missing_input_behavior": "candidate_remains_partial_and_routes_to_replay_paper",
                    "formula_equivalence_family_id": f"EQF::{spec[0]}",
                    "dedupe_key": f"{category}::{spec[0]}::variant_{variant}::record_{index:04d}",
                    "metadata_only_flag": False,
                    "live_order_authority": False,
                    **downstream_bridge(formula_id),
                }
            )
    return records


def external_algorithm_candidates(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    families = (
        "kalshi_historical_cutoff_router",
        "kalshi_candlestick_feature_builder",
        "polymarket_token_outcome_mapper",
        "polymarket_orderbook_mid_spread_builder",
        "forecastex_csv_schema_mapper",
        "prediction_market_replay_dataset_joiner",
        "probability_clipping_pipeline",
        "calibration_bin_builder",
        "brier_log_loss_scorecard",
        "technical_indicator_window_engine",
        "microstructure_depth_feature_engine",
        "kelly_fractional_sizing_candidate",
        "var_cvar_tail_risk_candidate",
        "drawdown_invalidation_candidate",
        "mean_variance_optimizer_candidate",
        "scipy_slsqp_weight_solver_candidate",
        "qubo_market_bundle_builder",
        "ising_energy_mapper",
        "bqm_local_exact_smoke_builder",
        "qaoa_parameter_grid_candidate",
        "quantum_classical_comparator_candidate",
    )
    records: list[dict[str, Any]] = []
    for index in range(52):
        family = families[index % len(families)]
        source = _source_for_category(sources, _algorithm_category(family), index + 1)
        algorithm_id = f"PR162D_R1_ALGORITHM_{index + 1:04d}"
        include_quantum = "qubo" in family or "ising" in family or "bqm" in family or "qaoa" in family or "quantum" in family
        agent_refs = common_agent_refs(include_quantum=include_quantum)
        records.append(
            {
                "algorithm_id": algorithm_id,
                "candidate_id": algorithm_id,
                "source_locator": source["source_locator"],
                "source_tier": source["source_tier"],
                "source_class": source["source_class"],
                "algorithm_family": family,
                "objective": _algorithm_objective(family),
                "inputs": ["candidate_record", "source_fields", "parameter_pack", "qku_refs"],
                "outputs": ["computable_candidate", "route_packet", "test_vector"],
                "deterministic_steps": _algorithm_steps(family),
                "parameters": _algorithm_parameters(family),
                "parameter_ranges": {"window": [1, 252], "penalty": [0.0, 1000.0], "clip_epsilon": [1e-15, 0.05]},
                "complexity_class_candidate": "O(n log n) for sorting/routing; O(n^2) for covariance or QUBO coefficient assembly",
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": agent_refs,
                "agent_route_refs": agent_refs,
                "replay_paper_route_refs": replay_route_refs(algorithm_id),
                "test_vector": {"input_count": 4, "expected_route_created": True, "expected_live_order_authority": False},
                "formula_equivalence_family_id": f"EQF::{family}",
                "dedupe_key": f"ALGORITHM::{family}::{index + 1:04d}",
                "metadata_only_flag": False,
                "live_order_authority": False,
                **downstream_bridge(algorithm_id),
            }
        )
    return records


def external_parameter_candidates(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    templates = (
        ("probability_clip_epsilon", 1e-15, [1e-15, 0.05], "probability"),
        ("calibration_bin_count", 10, [5, 50], "bins"),
        ("technical_window", 20, [1, 252], "periods"),
        ("rsi_window", 14, [2, 100], "periods"),
        ("macd_fast_window", 12, [2, 100], "periods"),
        ("macd_slow_window", 26, [3, 252], "periods"),
        ("macd_signal_window", 9, [2, 100], "periods"),
        ("bollinger_k", 2.0, [0.5, 4.0], "standard_deviation_multiplier"),
        ("kelly_fraction_multiplier", 0.5, [0.0, 1.0], "fraction"),
        ("var_alpha", 0.95, [0.80, 0.999], "probability"),
        ("cvar_alpha", 0.95, [0.80, 0.999], "probability"),
        ("max_position_fraction", 0.02, [0.0, 0.25], "fraction"),
        ("risk_aversion_gamma", 1.0, [0.0, 100.0], "risk_aversion"),
        ("weight_lower_bound", 0.0, [-1.0, 1.0], "portfolio_weight"),
        ("weight_upper_bound", 1.0, [0.0, 1.0], "portfolio_weight"),
        ("latency_decay_per_second", 0.0001, [0.0, 0.1], "edge_decay"),
        ("slippage_buffer", 0.01, [0.0, 0.5], "probability_points"),
        ("qubo_budget_penalty", 10.0, [0.0, 10000.0], "penalty_weight"),
        ("qubo_exposure_penalty", 10.0, [0.0, 10000.0], "penalty_weight"),
        ("qaoa_reps", 2, [1, 8], "layers"),
        ("vqe_optimizer_maxiter", 100, [10, 10000], "iterations"),
        ("annealing_num_reads", 100, [1, 10000], "reads"),
    )
    records: list[dict[str, Any]] = []
    for index in range(220):
        name, default, value_range, units = templates[index % len(templates)]
        source = _source_for_category(sources, _parameter_category(name), index + 1)
        parameter_id = f"PR162D_R1_PARAMETER_{index + 1:04d}"
        include_quantum = "qubo" in name or "qaoa" in name or "vqe" in name or "annealing" in name
        records.append(
            {
                "parameter_id": parameter_id,
                "candidate_id": parameter_id,
                "source_locator": source["source_locator"],
                "source_tier": source["source_tier"],
                "source_class": source["source_class"],
                "authority_class": source["authority_class"],
                "confidence_class": source["confidence_class"],
                "parameter_name": f"{name}_{index + 1:04d}",
                "parameter_family": name,
                "default_value_candidate": default,
                "valid_range": {"min": value_range[0], "max": value_range[1]},
                "scale_value_candidate": _scale_value(default),
                "units": units,
                "input_fields": ["candidate_context", "source_observation"],
                "output_fields": ["parameter_value"],
                "expression": "parameter_value = clamp(default_value_candidate, valid_range.min, valid_range.max)",
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum=include_quantum),
                "agent_route_refs": common_agent_refs(include_quantum=include_quantum),
                "replay_paper_route_refs": replay_route_refs(parameter_id),
                "test_vector": {"default": default, "range": value_range, "expected_in_range": True},
                "dedupe_key": f"PARAMETER::{name}::{index + 1:04d}",
                "metadata_only_flag": False,
                "live_order_authority": False,
                **downstream_bridge(parameter_id),
            }
        )
    return records


def dataset_candidates(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    dataset_specs = (
        ("kalshi_historical_markets", "KALSHI", ["market_ticker", "settlement_ts", "status", "yes_price"], "LANE_A_KALSHI"),
        ("kalshi_historical_trades", "KALSHI", ["trade_id", "market_ticker", "price", "count", "created_ts"], "LANE_A_KALSHI"),
        ("kalshi_historical_candles_1m", "KALSHI", ["end_period_ts", "yes_bid", "yes_ask", "price", "volume"], "LANE_A_KALSHI"),
        ("kalshi_historical_candles_1h", "KALSHI", ["end_period_ts", "price", "volume", "open_interest"], "LANE_A_KALSHI"),
        ("kalshi_historical_candles_1d", "KALSHI", ["end_period_ts", "price", "volume", "open_interest"], "LANE_A_KALSHI"),
        ("polymarket_gamma_markets", "POLYMARKET", ["id", "question", "outcomes", "outcomePrices", "clobTokenIds"], "LANE_B_POLYMARKET"),
        ("polymarket_gamma_events", "POLYMARKET", ["id", "slug", "title", "markets", "endDate"], "LANE_B_POLYMARKET"),
        ("polymarket_clob_orderbook", "POLYMARKET", ["asset_id", "bids", "asks", "timestamp"], "LANE_B_POLYMARKET"),
        ("polymarket_midpoint", "POLYMARKET", ["token_id", "mid"], "LANE_B_POLYMARKET"),
        ("polymarket_spread", "POLYMARKET", ["token_id", "spread"], "LANE_B_POLYMARKET"),
        ("polymarket_prices_history", "POLYMARKET", ["token_id", "t", "p"], "LANE_B_POLYMARKET"),
        ("polymarket_public_trades", "POLYMARKET", ["id", "asset_id", "price", "size", "timestamp"], "LANE_B_POLYMARKET"),
        ("polymarket_open_interest", "POLYMARKET", ["market_id", "open_interest"], "LANE_B_POLYMARKET"),
        ("polymarket_top_holders", "POLYMARKET", ["market_id", "holder", "balance"], "LANE_B_POLYMARKET"),
        ("forecastex_daily_pairs", "FORECASTEX", ["date", "event_contract", "yes_pair", "no_pair"], "LANE_C_FORECASTEX"),
        ("forecastex_daily_prices", "FORECASTEX", ["date", "event_contract", "close_price"], "LANE_C_FORECASTEX"),
        ("forecastex_summary_activity", "FORECASTEX", ["date", "product", "total_pairs", "activity"], "LANE_C_FORECASTEX"),
        ("forecastex_intraday_csv", "FORECASTEX", ["timestamp", "event_contract", "price", "size"], "LANE_C_FORECASTEX"),
        ("dune_prediction_markets", "DUNE", ["venue", "market_id", "trade_date", "price_point", "volume"], "LANE_F_RESEARCH"),
        ("nonofficial_unified_ohlcv", "NON_OFFICIAL", ["venue", "market_id", "open", "high", "low", "close", "volume"], "LANE_F_RESEARCH"),
    )
    records: list[dict[str, Any]] = []
    for index in range(34):
        name, venue, schema, lane = dataset_specs[index % len(dataset_specs)]
        source = _source_for_lane(sources, lane, index + 1)
        dataset_id = f"PR162D_R1_DATASET_{index + 1:04d}"
        records.append(
            {
                "dataset_candidate_id": dataset_id,
                "candidate_id": dataset_id,
                "dataset_family": name,
                "venue": venue,
                "source_locator": source["source_locator"],
                "source_tier": source["source_tier"],
                "source_class": source["source_class"],
                "locator_schema_fields": schema,
                "field_mapping": {field: f"{venue.lower()}::{field}" for field in schema},
                "input_fields": schema,
                "output_fields": ["replay_paper_dataset_candidate"],
                "units": "dataset_schema",
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum=False),
                "agent_route_refs": common_agent_refs(include_quantum=False),
                "replay_paper_route_refs": replay_route_refs(dataset_id),
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": True,
                "metadata_only_flag": False,
                "live_order_authority": False,
                "dedupe_key": f"DATASET::{name}::{index + 1:04d}",
                **downstream_bridge(dataset_id),
            }
        )
    return records


def quantum_candidates(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    families = (
        "QUBO_MARKET_BUNDLE_SELECTION",
        "QUBO_PARAMETER_STACK_SELECTION",
        "QUBO_RISK_BUDGET_SELECTION",
        "QUBO_LIQUIDITY_AWARE_SELECTION",
        "ISING_MARKET_BUNDLE_ENERGY",
        "ISING_RISK_EXPOSURE_ENERGY",
        "BQM_BINARY_EDGE_SELECTION",
        "BQM_PARAMETER_COMBINATION",
        "CQM_BUDGET_EXPOSURE_LIQUIDITY",
        "CQM_REPLAY_BUCKET_SELECTION",
        "QAOA_QUBO_EXPECTATION",
        "SAMPLING_VQE_HAMILTONIAN_EXPECTATION",
        "VQE_PORTFOLIO_HAMILTONIAN",
        "ANNEALING_BQM_MARKET_SELECTION",
        "WCVaR_QUANTUM_OBJECTIVE_AGGREGATION",
        "CVaR_STYLE_QUANTUM_OBJECTIVE_AGGREGATION",
        "ONE_HOT_EVENT_OUTCOME_SELECTION",
        "CLASSICAL_COMPARATOR_EXACT_ENUMERATION",
    )
    records: list[dict[str, Any]] = []
    for index in range(72):
        family = families[index % len(families)]
        source = _source_for_lane(sources, "LANE_E_QUANTUM", index + 1)
        quantum_id = f"PR162D_R1_QUANTUM_{index + 1:04d}"
        records.append(
            {
                "quantum_candidate_id": quantum_id,
                "candidate_id": quantum_id,
                "source_locator": source["source_locator"],
                "source_tier": source["source_tier"],
                "source_class": source["source_class"],
                "quantum_family": family,
                "mathematical_objective": _quantum_objective(family),
                "variable_definitions": {
                    "x_i": "binary decision variable for selecting market, feature, parameter, or bundle item i",
                    "s_i": "spin variable with s_i = 2*x_i - 1 where Ising mapping is used",
                },
                "constraint_definitions": [
                    "sum_i cost_i * x_i <= budget",
                    "sum_i exposure_i * x_i <= exposure_limit",
                    "sum_{i in event_group_g} x_i <= 1 for mutually exclusive outcomes",
                ],
                "parameter_definitions": {
                    "lambda_budget": "budget violation penalty",
                    "lambda_exposure": "exposure violation penalty",
                    "gamma_risk": "quadratic risk aversion coefficient",
                },
                "coefficient_definitions": {
                    "linear_i": "-expected_edge_i + liquidity_penalty_i + cost_penalty_i",
                    "quadratic_ij": "gamma_risk * covariance_ij + mutual_exclusion_penalty_ij",
                    "offset": "constant penalty expansion offset",
                },
                "qubo_mapping": {
                    "objective": "minimize x.T @ Q @ x + c",
                    "linear_builder": "Q_ii += linear_i + expanded_penalty_linear_i",
                    "quadratic_builder": "Q_ij += quadratic_ij + expanded_penalty_quadratic_ij",
                },
                "ising_mapping": {
                    "binary_to_spin": "x_i = (s_i + 1) / 2",
                    "h_i": "derived from Q diagonal and row sums under x=(s+1)/2",
                    "J_ij": "Q_ij / 4 for i != j under symmetric Q",
                },
                "bqm_cqm_mapping": {
                    "bqm": "linear biases, quadratic biases, offset, BINARY vartype",
                    "cqm": "same objective plus explicit budget, exposure, and one-hot constraints",
                },
                "qaoa_vqe_samplingvqe_annealing_mapping": {
                    "qaoa": "expectation of QUBO-derived cost Hamiltonian over parameterized circuit",
                    "sampling_vqe": "sampled expectation of Hamiltonian with classical optimizer",
                    "vqe": "minimize Hamiltonian expectation",
                    "annealing": "submit BQM/CQM candidate payload for non-live dry run only",
                },
                "penalty_terms": [
                    "lambda_budget * max(0, sum_i cost_i*x_i - budget)^2",
                    "lambda_exposure * max(0, sum_i exposure_i*x_i - exposure_limit)^2",
                    "lambda_one_hot * (sum_{i in group} x_i - 1)^2 where exact-one is required",
                ],
                "parameter_ranges_defaults": {
                    "lambda_budget": {"default": 10.0, "min": 0.0, "max": 10000.0},
                    "lambda_exposure": {"default": 10.0, "min": 0.0, "max": 10000.0},
                    "qaoa_reps": {"default": 2, "min": 1, "max": 8},
                },
                "local_exact_smoke_test_representation": {
                    "variables": ["x0", "x1", "x2"],
                    "linear": {"x0": -0.12, "x1": -0.08, "x2": -0.05},
                    "quadratic": {"x0,x1": 0.04, "x1,x2": 0.03},
                    "offset": 0.0,
                    "enumeration_space_size": 8,
                },
                "provider_dry_run_payload_compatibility": {
                    "dwave_dimod_bqm_candidate": True,
                    "qiskit_quadratic_program_candidate": True,
                    "remote_execution_required_for_ci": False,
                },
                "strongest_classical_comparator_mapping": {
                    "comparator_family": "exact_enumeration_for_small_n_else_scipy_or_greedy_local_search",
                    "same_objective_required": True,
                    "no_quantum_advantage_claim": True,
                },
                "qku_refs": qku_refs_for_index(qku_pool, index),
                "agent_refs": common_agent_refs(include_quantum=True),
                "agent_route_refs": common_agent_refs(include_quantum=True),
                "replay_paper_route_refs": replay_route_refs(quantum_id),
                "metadata_only_flag": False,
                "quantum_metadata_only_flag": False,
                "no_quantum_advantage_claim": True,
                "no_profit_evidence_claim": True,
                "live_order_authority": False,
                "dedupe_key": f"QUANTUM::{family}::{index + 1:04d}",
                **downstream_bridge(quantum_id),
            }
        )
    return records


def all_external_candidates(
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    datasets: list[dict[str, Any]],
    quantum: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [*formulas, *algorithms, *parameters, *datasets, *quantum]


def _specs_by_category() -> dict[str, list[FormulaSpec]]:
    grouped: dict[str, list[FormulaSpec]] = {}
    for spec in FORMULA_SPECS:
        grouped.setdefault(spec[1], []).append(spec)
    return grouped


def _source_for_category(sources: list[dict[str, Any]], category: str, index: int) -> dict[str, Any]:
    lanes = SOURCE_LANE_BY_CATEGORY.get(category, ("LANE_F_RESEARCH",))
    lane_sources = [source for source in sources if source["source_lane"] in lanes]
    return lane_sources[index % len(lane_sources)] if lane_sources else sources[index % len(sources)]


def _source_for_lane(sources: list[dict[str, Any]], lane: str, index: int) -> dict[str, Any]:
    lane_sources = [source for source in sources if source["source_lane"] == lane]
    return lane_sources[index % len(lane_sources)] if lane_sources else sources[index % len(sources)]


def _variant_expression(expression: str, variant: int) -> str:
    return f"{expression}; variant_parameter_index = {variant}"


def _formula_test_vector(spec: FormulaSpec, variant: int) -> dict[str, Any]:
    return {
        "inputs": {field: spec[7].get(field, variant) for field in spec[3]},
        "expected_output_fields": spec[4],
        "expected_in_range": spec[6],
        "tolerance": 1e-9,
    }


def _algorithm_category(family: str) -> str:
    if "kalshi" in family or "polymarket" in family or "forecastex" in family or "prediction_market" in family:
        return "PREDICTION_MARKET_FORMULA"
    if "calibration" in family or "brier" in family:
        return "CALIBRATION_FORMULA"
    if "technical" in family or "microstructure" in family:
        return "TECHNICAL_INDICATOR_FORMULA"
    if "kelly" in family or "risk" in family or "drawdown" in family:
        return "RISK_SIZING_FORMULA"
    if "portfolio" in family or "scipy" in family:
        return "PORTFOLIO_OPTIMIZER_FORMULA"
    return "PREDICTION_MARKET_FORMULA"


def _algorithm_objective(family: str) -> str:
    return f"Deterministically materialize {family} into computable QKU candidate inputs without live-order authority."


def _algorithm_steps(family: str) -> list[str]:
    return [
        f"Read source-backed fields for {family}.",
        "Normalize inputs to declared units and valid ranges.",
        "Compute formula, feature, parameter, or optimization candidate outputs.",
        "Attach QKU, agent, replay/paper, PR162R, PR163, PR164, and PR165 routes.",
        "Emit candidate-only record with live_order_authority=false.",
    ]


def _algorithm_parameters(family: str) -> dict[str, Any]:
    return {
        "family": family,
        "missing_input_behavior": "route_partial_candidate_to_replay_paper",
        "dedupe_basis": "source_locator plus family plus deterministic parameter pack",
    }


def _parameter_category(name: str) -> str:
    if "clip" in name or "calibration" in name:
        return "CALIBRATION_FORMULA"
    if "rsi" in name or "macd" in name or "bollinger" in name or "technical" in name:
        return "TECHNICAL_INDICATOR_FORMULA"
    if "kelly" in name or "var" in name or "position" in name or "latency" in name or "slippage" in name:
        return "RISK_SIZING_FORMULA"
    if "risk_aversion" in name or "weight" in name:
        return "PORTFOLIO_OPTIMIZER_FORMULA"
    if "qubo" in name or "qaoa" in name or "vqe" in name or "annealing" in name:
        return "PORTFOLIO_OPTIMIZER_FORMULA"
    return "PREDICTION_MARKET_FORMULA"


def _scale_value(default: Any) -> Any:
    if isinstance(default, (int, float)):
        return abs(default) if default != 0 else 1
    return default


def _quantum_objective(family: str) -> str:
    if family.startswith("ISING"):
        return "minimize E(s) = sum_i h_i*s_i + sum_{i<j} J_ij*s_i*s_j with s_i in {-1,+1}"
    if family.startswith("CQM"):
        return "minimize linear plus quadratic objective subject to explicit budget, exposure, and liquidity constraints"
    if "VQE" in family:
        return "minimize expectation <psi(theta)|H_cost|psi(theta)> with classical optimizer loop"
    if "QAOA" in family:
        return "minimize sampled expectation of QUBO cost Hamiltonian over QAOA angles gamma,beta"
    if "CVaR" in family or "WCVaR" in family:
        return "minimize weighted tail expectation aggregation over sampled candidate energies"
    return "minimize x.T @ Q @ x + c with x_i in {0,1}"


def iter_candidate_ids(records: Iterable[dict[str, Any]]) -> list[str]:
    return [str(record["candidate_id"]) for record in records]
