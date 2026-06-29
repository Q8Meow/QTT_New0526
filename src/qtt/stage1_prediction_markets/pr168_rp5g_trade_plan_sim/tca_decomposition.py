"""Implementation-shortfall-style TCA decomposition."""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from .models import dec, score

TCA_COMPONENTS = (
    "fees_cash",
    "spread_cost_cash",
    "slippage_cash",
    "latency_penalty_cash",
    "market_impact_cash",
    "opportunity_cost_cash",
    "cancel_replace_cost_cash",
    "cashflow_settlement_cost_cash",
)


def compute_tca_total(components: Mapping[str, Decimal | int | str | float]) -> Decimal:
    return sum((dec(components.get(name, 0)) for name in TCA_COMPONENTS), Decimal("0"))


def implementation_shortfall_components(
    *,
    order_size_contracts: int,
    entry_price_dec: Decimal,
    spread_bucket: str,
    liquidity_bucket: str,
    maker_taker_policy: str,
    latency_ms: int,
    hold_hours: Decimal,
) -> dict[str, Decimal]:
    size = dec(order_size_contracts)
    spread_rate = {"TIGHT": Decimal("0.002"), "MEDIUM": Decimal("0.006"), "NORMAL": Decimal("0.005"), "WIDE": Decimal("0.015")}.get(spread_bucket, Decimal("0.020"))
    liq_rate = {"HIGH": Decimal("0.001"), "MEDIUM": Decimal("0.004"), "LOW": Decimal("0.010"), "BLOCKED": Decimal("0.050")}.get(liquidity_bucket, Decimal("0.015"))
    taker_fee = Decimal("0.006") if maker_taker_policy in {"TAKER_ONLY", "TAKER_AFTER_TIMEOUT"} else Decimal("0.0025")
    cancel_cost = Decimal("0.0002") * size if "CANCEL" in maker_taker_policy or "MAKER" in maker_taker_policy else Decimal("0")
    base_notional = size * entry_price_dec
    return {
        "fees_cash": taker_fee * size,
        "spread_cost_cash": spread_rate * base_notional,
        "slippage_cash": liq_rate * base_notional,
        "latency_penalty_cash": Decimal(str(latency_ms)) * Decimal("0.000004") * size,
        "market_impact_cash": liq_rate * Decimal("0.5") * size,
        "opportunity_cost_cash": Decimal("0.001") * size if maker_taker_policy != "TAKER_ONLY" else Decimal("0.0002") * size,
        "cancel_replace_cost_cash": cancel_cost,
        "cashflow_settlement_cost_cash": Decimal("0.00001") * hold_hours * size,
    }


def scored_components(components: Mapping[str, Decimal | int | str | float]) -> dict[str, str]:
    payload = {name: score(components.get(name, 0)) for name in TCA_COMPONENTS}
    payload["TCA_total_cash"] = score(compute_tca_total(components))
    return payload

