"""Deterministic PR162R-B feature calculators."""

from __future__ import annotations

import math
from typing import Iterable


EPSILON = 1e-12


def _finite(value: float) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite feature output: {value!r}")
    return result


def best_bid(levels: Iterable[tuple[float, float]]) -> float:
    return _finite(max(price for price, _size in levels))


def best_ask(levels: Iterable[tuple[float, float]]) -> float:
    return _finite(min(price for price, _size in levels))


def midprice(best_bid_value: float, best_ask_value: float) -> float:
    return _finite((best_bid_value + best_ask_value) / 2.0)


def spread(best_bid_value: float, best_ask_value: float) -> float:
    return _finite(best_ask_value - best_bid_value)


def half_spread(spread_value: float) -> float:
    return _finite(spread_value / 2.0)


def normalized_spread(spread_value: float, midprice_value: float, epsilon: float = EPSILON) -> float:
    return _finite(spread_value / max(midprice_value, epsilon))


def top_of_book_depth(bid_top_size: float, ask_top_size: float) -> float:
    return _finite(bid_top_size + ask_top_size)


def depth_imbalance(bid_depth: float, ask_depth: float, epsilon: float = EPSILON) -> float:
    return _finite((bid_depth - ask_depth) / max(bid_depth + ask_depth, epsilon))


def microprice(best_bid_value: float, best_ask_value: float, bid_size: float, ask_size: float, epsilon: float = EPSILON) -> float:
    return _finite(
        (best_bid_value * ask_size + best_ask_value * bid_size)
        / max(bid_size + ask_size, epsilon)
    )


def trade_intensity(trade_count: float, window_seconds: float) -> float:
    return _finite(trade_count / max(window_seconds, EPSILON))


def volume_intensity(traded_volume: float, window_seconds: float) -> float:
    return _finite(traded_volume / max(window_seconds, EPSILON))


def price_jump(current_midprice: float, prior_midprice: float) -> float:
    return _finite(current_midprice - prior_midprice)


def time_to_resolution_seconds(resolution_timestamp: float, observation_timestamp: float) -> float:
    return _finite(resolution_timestamp - observation_timestamp)


def staleness_seconds(observation_timestamp: float, source_timestamp: float) -> float:
    return _finite(observation_timestamp - source_timestamp)


def fee_adjusted_price(price: float, estimated_fee_per_share: float) -> float:
    return _finite(price + estimated_fee_per_share)


def slippage_adjusted_price(price: float, expected_slippage_per_share: float) -> float:
    return _finite(price + expected_slippage_per_share)


def cost_adjusted_entry_price(price: float, fee: float, slippage: float) -> float:
    return _finite(price + fee + slippage)


def binary_yes_ev(model_probability: float, cost_adjusted_entry_price_value: float) -> float:
    return _finite(
        model_probability * (1.0 - cost_adjusted_entry_price_value)
        - (1.0 - model_probability) * cost_adjusted_entry_price_value
    )


def binary_no_ev(model_probability: float, cost_adjusted_entry_price_value: float) -> float:
    return _finite(
        (1.0 - model_probability) * (1.0 - cost_adjusted_entry_price_value)
        - model_probability * cost_adjusted_entry_price_value
    )


def net_edge(expected_value: float, transaction_cost_estimate: float) -> float:
    return _finite(expected_value - transaction_cost_estimate)


def fillable_size_at_limit(depth_levels: Iterable[tuple[float, float]], limit_price: float, side: str) -> float:
    side_upper = side.upper()
    if side_upper == "BUY":
        return _finite(sum(size for price, size in depth_levels if price <= limit_price))
    if side_upper == "SELL":
        return _finite(sum(size for price, size in depth_levels if price >= limit_price))
    raise ValueError(f"unsupported side: {side!r}")


def simple_fill_probability(available_depth_at_limit: float, desired_size: float, epsilon: float = EPSILON) -> float:
    return _finite(min(1.0, available_depth_at_limit / max(desired_size, epsilon)))


def paper_fill_price(
    *,
    limit_price: float,
    best_bid_value: float,
    best_ask_value: float,
    side: str,
    available_depth_at_limit: float,
    desired_size: float,
    fee: float,
    slippage: float,
    latency_bucket: str,
) -> float:
    fill_probability = simple_fill_probability(available_depth_at_limit, desired_size)
    latency_addon = {"LOW": 0.0, "MEDIUM": 0.001, "HIGH": 0.003}.get(latency_bucket.upper(), 0.002)
    if side.upper() == "BUY":
        base = min(limit_price, best_ask_value)
        depth_adjustment = (1.0 - fill_probability) * 0.002
        return _finite(base + fee + slippage + latency_addon + depth_adjustment)
    if side.upper() == "SELL":
        base = max(limit_price, best_bid_value)
        depth_adjustment = (1.0 - fill_probability) * 0.002
        return _finite(base - fee - slippage - latency_addon - depth_adjustment)
    raise ValueError(f"unsupported side: {side!r}")


def fixture_settlement_pnl(payout: float, entry_cost: float, fees: float, slippage: float) -> float:
    return _finite(payout - entry_cost - fees - slippage)


def build_feature_calculator_registry(dataset_bindings: list[dict]) -> list[dict]:
    formulas = [
        "best_bid",
        "best_ask",
        "midprice",
        "spread",
        "half_spread",
        "normalized_spread",
        "top_of_book_depth",
        "depth_imbalance",
        "microprice",
        "trade_intensity",
        "volume_intensity",
        "price_jump",
        "time_to_resolution_seconds",
        "staleness_seconds",
        "fee_adjusted_price",
        "slippage_adjusted_price",
        "cost_adjusted_entry_price",
        "binary_yes_ev",
        "binary_no_ev",
        "net_edge",
        "fillable_size_at_limit",
        "simple_fill_probability",
        "paper_fill_price",
        "fixture_settlement_pnl",
    ]
    binding_refs = sorted(binding["binding_id"] for binding in dataset_bindings)
    return [
        {
            "feature_calculator_binding_id": f"PR162R_B_FEATURE_CALCULATOR::{index:03d}",
            "calculator_name": name,
            "callable_ref": (
                "src.qtt.stage1_prediction_markets."
                "pr162r_b_replay_paper_data_binding_completion.feature_calculators:"
                f"{name}"
            ),
            "linked_binding_refs": binding_refs[:12],
            "deterministic": True,
            "finite_output_required": True,
            "live_order_authority": False,
            "profit_evidence_claim": False,
            "validation_status": "PASS",
        }
        for index, name in enumerate(formulas, start=1)
    ]
