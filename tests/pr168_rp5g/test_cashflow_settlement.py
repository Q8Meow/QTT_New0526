from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.cashflow_settlement import capital_lock_cost


def test_capital_lock_cost() -> None:
    assert capital_lock_cost(10, Decimal("2")) == Decimal("0.000200")

