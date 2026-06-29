from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.expected_pnl import gross_edge_per_contract, expected_gross_pnl_cash


def test_expected_pnl_formula() -> None:
    edge = gross_edge_per_contract(Decimal("0.60"), Decimal("0.45"))
    assert edge == Decimal("0.15")
    assert expected_gross_pnl_cash(10, Decimal("1"), edge) == Decimal("1.50")

