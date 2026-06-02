"""Technical and market-microstructure feature formulas for PR162B."""

from __future__ import annotations

import math


def _values(values: list[float] | tuple[float, ...], name: str = "values") -> list[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def simple_moving_average(values: list[float] | tuple[float, ...], window: int) -> float:
    xs = _values(values)
    if window <= 0 or window > len(xs):
        raise ValueError("window must be positive and no larger than values length")
    return sum(xs[-window:]) / window


def exponential_moving_average(values: list[float] | tuple[float, ...], span: int) -> float:
    xs = _values(values)
    if span <= 0:
        raise ValueError("span must be positive")
    alpha = 2.0 / (span + 1.0)
    ema = xs[0]
    for value in xs[1:]:
        ema = alpha * value + (1.0 - alpha) * ema
    return ema


def z_score(value: float, mean: float, std: float) -> float:
    denominator = float(std)
    if denominator <= 0.0:
        raise ValueError("std must be positive")
    return (float(value) - float(mean)) / denominator


def spread(ask: float, bid: float) -> float:
    result = float(ask) - float(bid)
    if result < 0.0:
        raise ValueError("ask must be greater than or equal to bid")
    return result


def midpoint(ask: float, bid: float) -> float:
    spread(ask, bid)
    return (float(ask) + float(bid)) / 2.0


def momentum(values: list[float] | tuple[float, ...], window: int) -> float:
    xs = _values(values)
    if window <= 0 or window >= len(xs):
        raise ValueError("window must be positive and smaller than values length")
    return xs[-1] - xs[-1 - window]


def realized_volatility(returns: list[float] | tuple[float, ...], annualization_factor: float = 1.0) -> float:
    xs = _values(returns, "returns")
    mean = sum(xs) / len(xs)
    variance = sum((value - mean) ** 2 for value in xs) / len(xs)
    return math.sqrt(variance) * math.sqrt(float(annualization_factor))


def rsi(values: list[float] | tuple[float, ...], period: int = 14) -> float:
    xs = _values(values)
    if period <= 0 or len(xs) <= period:
        raise ValueError("values length must be greater than period")
    deltas = [b - a for a, b in zip(xs[-period - 1 : -1], xs[-period:], strict=True)]
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [abs(min(delta, 0.0)) for delta in deltas]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0.0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(
    values: list[float] | tuple[float, ...],
    fast_span: int = 12,
    slow_span: int = 26,
    signal_span: int = 9,
) -> dict[str, float]:
    xs = _values(values)
    if not (0 < fast_span < slow_span <= len(xs)):
        raise ValueError("spans must satisfy 0 < fast_span < slow_span <= values length")
    macd_series: list[float] = []
    for index in range(slow_span, len(xs) + 1):
        segment = xs[:index]
        macd_series.append(
            exponential_moving_average(segment, fast_span)
            - exponential_moving_average(segment, slow_span)
        )
    line = macd_series[-1]
    signal = exponential_moving_average(macd_series, min(signal_span, len(macd_series)))
    return {"macd": line, "signal": signal, "histogram": line - signal}


def bollinger_bands(
    values: list[float] | tuple[float, ...],
    window: int = 20,
    num_std: float = 2.0,
) -> dict[str, float]:
    xs = _values(values)
    if window <= 0 or window > len(xs):
        raise ValueError("window must be positive and no larger than values length")
    segment = xs[-window:]
    middle = sum(segment) / window
    std = math.sqrt(sum((value - middle) ** 2 for value in segment) / window)
    width = float(num_std) * std
    return {"lower": middle - width, "middle": middle, "upper": middle + width}


def vwap(prices: list[float] | tuple[float, ...], volumes: list[float] | tuple[float, ...]) -> float:
    ps = _values(prices, "prices")
    vs = _values(volumes, "volumes")
    if len(ps) != len(vs):
        raise ValueError("prices and volumes must have equal length")
    denominator = sum(vs)
    if denominator <= 0.0:
        raise ValueError("sum of volumes must be positive")
    return sum(price * volume for price, volume in zip(ps, vs, strict=True)) / denominator


def orderbook_imbalance_candidate(bid_size: float, ask_size: float) -> float:
    bid = float(bid_size)
    ask = float(ask_size)
    total = bid + ask
    if total <= 0.0:
        raise ValueError("bid_size + ask_size must be positive")
    return (bid - ask) / total


def liquidity_proxy_candidate(volume: float, spread_value: float, epsilon: float = 1e-9) -> float:
    return float(volume) / max(float(spread_value), float(epsilon))
