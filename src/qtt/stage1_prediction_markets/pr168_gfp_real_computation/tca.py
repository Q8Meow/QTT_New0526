"""Transaction cost analysis formulas for PR168-GFP."""

from __future__ import annotations


def tca_decomposition(
    explicit_fees: float = 0.0,
    spread_cost: float = 0.0,
    slippage: float = 0.0,
    market_impact: float = 0.0,
    adverse_selection_penalty: float = 0.0,
    implementation_shortfall: float = 0.0,
    nonfill_or_opportunity_cost: float = 0.0,
) -> dict[str, float]:
    components = {
        "explicit_fees": float(explicit_fees),
        "spread_cost": float(spread_cost),
        "slippage": float(slippage),
        "market_impact": float(market_impact),
        "adverse_selection_penalty": float(adverse_selection_penalty),
        "implementation_shortfall": float(implementation_shortfall),
        "nonfill_or_opportunity_cost": float(nonfill_or_opportunity_cost),
    }
    components["total_tca_cost"] = sum(components.values())
    return components
