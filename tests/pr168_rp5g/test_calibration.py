from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.calibration import calibration_gap


def test_calibration_gap_abs() -> None:
    assert calibration_gap(Decimal("0.55"), Decimal("0.50")) == Decimal("0.05")

