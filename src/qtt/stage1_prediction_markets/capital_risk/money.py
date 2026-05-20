from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Mapping


DEFAULT_CURRENCY_SCALES: Mapping[str, int] = {"USD": 2}


def decimal_from_string(value: str) -> Decimal:
    if isinstance(value, float):
        raise TypeError("binary float is forbidden for fixture cash math")
    if not isinstance(value, str):
        raise TypeError("fixture cash values must be strings")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid Decimal cash amount: {value!r}") from exc


def quantize_cash_amount(
    amount: Decimal,
    currency: str,
    *,
    currency_scales: Mapping[str, int] = DEFAULT_CURRENCY_SCALES,
) -> Decimal:
    if not isinstance(amount, Decimal):
        raise TypeError("cash amount must be Decimal")
    scale = currency_scales.get(currency)
    if scale is None:
        raise ValueError(f"missing deterministic currency scale for {currency}")
    quantum = Decimal("1").scaleb(-scale)
    return amount.quantize(quantum, rounding=ROUND_HALF_EVEN)


def money(amount: Decimal | str, currency: str = "USD") -> dict[str, str]:
    value = decimal_from_string(amount) if isinstance(amount, str) else amount
    return {"amount": format(quantize_cash_amount(value, currency), "f"), "currency": currency}


def money_decimal(value: Mapping[str, str]) -> Decimal:
    return decimal_from_string(value["amount"])


def assert_same_currency(*values: Mapping[str, str]) -> str:
    currencies = {value["currency"] for value in values}
    if len(currencies) != 1:
        raise ValueError(f"mixed currencies are forbidden: {sorted(currencies)}")
    return next(iter(currencies))
