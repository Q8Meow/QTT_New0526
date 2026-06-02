"""PR162C technical feature formula deltas."""

from __future__ import annotations


def time_to_resolution_seconds(observation_ts: float, resolution_ts: float) -> float:
    return max(0.0, float(resolution_ts) - float(observation_ts))


def price_momentum(current_price: float, previous_price: float) -> float:
    return float(current_price) - float(previous_price)


def volume_momentum(current_volume: float, previous_volume: float) -> float:
    return float(current_volume) - float(previous_volume)


def spread_change(current_spread: float, previous_spread: float) -> float:
    return float(current_spread) - float(previous_spread)


def orderbook_depth_proxy(bid_size: float, ask_size: float) -> float:
    if bid_size < 0.0 or ask_size < 0.0:
        raise ValueError("sizes must be non-negative")
    return float(bid_size) + float(ask_size)


def liquidity_score(volume: float, spread: float, epsilon: float = 1e-9) -> float:
    if volume < 0.0:
        raise ValueError("volume must be non-negative")
    return float(volume) / max(float(spread), float(epsilon))
