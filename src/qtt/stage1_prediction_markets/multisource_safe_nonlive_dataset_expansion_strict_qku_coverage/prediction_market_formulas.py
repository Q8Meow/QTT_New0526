"""PR162C deterministic prediction-market formula deltas."""

from __future__ import annotations


def _probability(value: float, name: str) -> float:
    result = float(value)
    if result < 0.0 or result > 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return result


def yes_contract_ev(p_model: float, ask_price_yes_adjusted: float, payout: float = 1.0) -> float:
    return _probability(p_model, "p_model") * float(payout) - _probability(
        ask_price_yes_adjusted,
        "ask_price_yes_adjusted",
    )


def no_contract_ev(p_model: float, ask_price_no_adjusted: float, payout: float = 1.0) -> float:
    return (1.0 - _probability(p_model, "p_model")) * float(payout) - _probability(
        ask_price_no_adjusted,
        "ask_price_no_adjusted",
    )


def expected_net_profit(expected_value: float, fees: float, slippage: float, latency_penalty: float) -> float:
    return float(expected_value) - float(fees) - float(slippage) - float(latency_penalty)


def edge_yes(p_model: float, ask_price_yes_adjusted: float) -> float:
    return _probability(p_model, "p_model") - _probability(
        ask_price_yes_adjusted,
        "ask_price_yes_adjusted",
    )


def edge_no(p_model: float, ask_price_no_adjusted: float) -> float:
    return (1.0 - _probability(p_model, "p_model")) - _probability(
        ask_price_no_adjusted,
        "ask_price_no_adjusted",
    )


def matched_yes_no_bundle_cost(yes_ask: float, no_ask: float) -> float:
    return _probability(yes_ask, "yes_ask") + _probability(no_ask, "no_ask")


def bounded_arbitrage_candidate_edge(yes_ask: float, no_ask: float, fee_buffer: float) -> float:
    return 1.0 - matched_yes_no_bundle_cost(yes_ask, no_ask) - float(fee_buffer)


def same_event_price_dislocation(price_a: float, price_b: float) -> float:
    return abs(_probability(price_a, "price_a") - _probability(price_b, "price_b"))


def liquidity_feasible_dislocation(dislocation: float, min_volume: float, observed_volume: float) -> bool:
    return float(dislocation) > 0.0 and float(observed_volume) >= float(min_volume)
