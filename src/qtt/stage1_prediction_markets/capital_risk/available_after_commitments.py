from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from src.qtt.stage1_prediction_markets.capital_risk.money import (
    assert_same_currency,
    money,
    money_decimal,
)


def compute_available_after_commitments_fixture(
    *,
    owner_policy_capital_remaining_for_venue_fixture: Mapping[str, str],
    runtime_verified_available_cash_fixture: Mapping[str, str],
    open_order_lock_total_fixture: Mapping[str, str],
    required_reserve_total_fixture: Mapping[str, str],
) -> dict[str, object]:
    currency = assert_same_currency(
        owner_policy_capital_remaining_for_venue_fixture,
        runtime_verified_available_cash_fixture,
        open_order_lock_total_fixture,
        required_reserve_total_fixture,
    )
    owner_remaining = money_decimal(owner_policy_capital_remaining_for_venue_fixture)
    verified_cash = money_decimal(runtime_verified_available_cash_fixture)
    open_order_lock = money_decimal(open_order_lock_total_fixture)
    required_reserve = money_decimal(required_reserve_total_fixture)
    after_open_orders_and_reserves = verified_cash - open_order_lock - required_reserve
    raw_available = min(owner_remaining, verified_cash, after_open_orders_and_reserves)
    available_for_exposure = max(Decimal("0"), raw_available)
    return {
        "runtime_available_after_open_orders_and_required_reserves_fixture": money(
            after_open_orders_and_reserves,
            currency,
        ),
        "raw_available_after_commitments_fixture": money(raw_available, currency),
        "available_after_commitments_for_new_exposure_fixture": money(
            available_for_exposure,
            currency,
        ),
        "negative_available_after_commitments_clamped_to_zero_flag": raw_available < Decimal("0"),
    }
