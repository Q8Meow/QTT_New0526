from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.fill_latency_capacity import fill_probability_for, partial_fill_ratio_for


def test_fill_probability_and_partial_fill_are_bounded() -> None:
    assert 0 <= fill_probability_for("HIGH", "TAKER_ONLY") <= 1
    assert 0 <= partial_fill_ratio_for("THIN", 100) <= 1

