import pytest

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.fill_queue_latency import (
    partial_fill,
    queue_fill_probability,
)


def test_queue_fill_probability_is_bounded_and_monotonic():
    low = queue_fill_probability(fill_intensity=2, time_horizon=1, queue_ahead=100, order_quantity=10)
    high = queue_fill_probability(fill_intensity=20, time_horizon=1, queue_ahead=100, order_quantity=10)

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0
    assert high > low


def test_partial_fill_ratio_is_bounded():
    assert partial_fill(25, 100) == 0.25
    assert partial_fill(150, 100) == 1.0
    assert partial_fill(-1, 100) == 0.0
