from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.tca_decomposition import compute_tca_total


def test_tca_total_sums_components() -> None:
    assert compute_tca_total({"fees_cash": Decimal("1"), "spread_cost_cash": Decimal("2")}) == Decimal("3")

