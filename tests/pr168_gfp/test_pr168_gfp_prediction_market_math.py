import pytest

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.prediction_market_math import (
    binary_contract_expected_value,
    expected_value,
    gross_edge,
    market_implied_probability,
)


def test_market_implied_probability_normalizes_and_clamps_price():
    assert market_implied_probability(57, {"price_multiplier": 100}, fee_adjustment=0.01) == 0.58
    assert market_implied_probability(1.4) == 1.0
    assert market_implied_probability(-0.1) == 0.0


def test_gross_edge_uses_predicted_minus_market_probability():
    assert gross_edge(0.62, 0.57) == pytest.approx(0.05)
    assert gross_edge(0.48, 0.52) == pytest.approx(-0.04)


def test_binary_contract_expected_value_uses_win_and_loss_legs():
    assert binary_contract_expected_value(0.62, 1.0, 0.38, 0.57) == 0.4034


def test_expected_value_sums_probability_weighted_payoffs():
    assert expected_value([0.25, 0.75], [-1.0, 2.0]) == 1.25
