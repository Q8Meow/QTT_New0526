from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.no_trade_comparator import compare_to_no_trade


def test_no_trade_wins_when_margin_nonpositive() -> None:
    assert compare_to_no_trade(Decimal("-0.1"))["no_trade_wins_flag"] is True
    assert compare_to_no_trade(Decimal("0.1"))["candidate_beats_no_trade_flag"] is True

