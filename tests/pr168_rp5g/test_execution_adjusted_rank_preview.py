from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.execution_adjusted_rank_preview import simulation_rank_score


def test_rank_score_prefers_positive_metrics() -> None:
    score = simulation_rank_score({"net_expected_pnl_cash": Decimal("1"), "lower_confidence_bound_pnl_cash": Decimal("0.5"), "no_trade_margin_cash": Decimal("1"), "fill_probability": Decimal("0.9"), "scenario_robustness_score": Decimal("1")})
    assert score > 0

