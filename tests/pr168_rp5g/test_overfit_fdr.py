from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.overfit_fdr import compute_fdr_penalty


def test_fdr_penalty_positive() -> None:
    penalty = compute_fdr_penalty(effective_trial_count=10, observed_edge_stability=Decimal("0.8"), validation_gap=Decimal("0.1"), calibration_gap=Decimal("0.1"), net_expected_pnl_cash=Decimal("1"))
    assert penalty > 0

