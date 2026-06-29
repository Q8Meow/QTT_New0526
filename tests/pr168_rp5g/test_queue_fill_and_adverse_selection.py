from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.adverse_selection import adverse_selection_penalty
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.queue_fill import partial_fill_ratio_for


def test_queue_and_adverse_selection_helpers() -> None:
    assert partial_fill_ratio_for("THIN", 30) == Decimal("0.5")
    assert adverse_selection_penalty(Decimal("-2")) == Decimal("0.120000")

