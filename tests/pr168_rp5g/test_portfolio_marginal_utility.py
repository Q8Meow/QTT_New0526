from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.portfolio_marginal_utility import compute_portfolio_marginal_utility


def test_portfolio_marginal_utility_formula() -> None:
    assert compute_portfolio_marginal_utility(diversification_benefit_cash=Decimal("1"), concentration_penalty_cash=Decimal("0.2"), correlation_proxy_penalty_cash=Decimal("0.3")) == Decimal("0.5")

