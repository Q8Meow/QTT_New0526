from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.capital_risk.money import (
    decimal_from_string,
    money,
)
from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_decimal_cash_math_is_deterministic_and_uses_no_binary_float():
    policy = support.field_map_report()["runtime_cash_decimal_policy"]

    assert policy["cash_math_type"] == "decimal.Decimal"
    assert policy["binary_float_cash_math_allowed"] is False
    assert policy["monetary_values_stored_as_strings"] is True
    assert money(Decimal("1.235"), "USD") == {"amount": "1.24", "currency": "USD"}
    with pytest.raises(TypeError):
        decimal_from_string(1.0)  # type: ignore[arg-type]
    assert support.main_report()["binary_float_cash_math_used"] is False
