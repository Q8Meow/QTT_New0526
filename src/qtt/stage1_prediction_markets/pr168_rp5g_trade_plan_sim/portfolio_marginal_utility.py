"""Portfolio marginal utility proxy without private account state."""

from __future__ import annotations

from decimal import Decimal

from .models import dec, score


def compute_portfolio_marginal_utility(
    *,
    diversification_benefit_cash: Decimal,
    concentration_penalty_cash: Decimal,
    correlation_proxy_penalty_cash: Decimal,
) -> Decimal:
    return diversification_benefit_cash - concentration_penalty_cash - correlation_proxy_penalty_cash


def portfolio_utility_summary(venue: str, event_category: str, standalone_expected_pnl_cash: Decimal) -> dict[str, str]:
    diversification = Decimal("0.020") if venue in {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"} else Decimal("0.000")
    concentration = Decimal("0.010") if event_category in {"politics", "rates"} else Decimal("0.006")
    correlation = max(dec(standalone_expected_pnl_cash).copy_abs() * Decimal("0.020"), Decimal("0.001"))
    utility = compute_portfolio_marginal_utility(
        diversification_benefit_cash=diversification,
        concentration_penalty_cash=concentration,
        correlation_proxy_penalty_cash=correlation,
    )
    return {
        "diversification_benefit_cash": score(diversification),
        "concentration_penalty_cash": score(concentration),
        "correlation_proxy_penalty_cash": score(correlation),
        "portfolio_marginal_utility_cash": score(utility),
        "portfolio_risk_penalty_cash": score(concentration + correlation),
    }

