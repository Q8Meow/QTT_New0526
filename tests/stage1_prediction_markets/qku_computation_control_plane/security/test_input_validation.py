from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    exact_decimal,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    compute_math_01_binary_implied_probability,
    compute_math_03_orderbook_midpoint,
    compute_math_06_binary_contract_expected_net_cash,
    compute_math_08_brier_score,
)


def test_numeric_boundaries_reject_float_nonfinite_and_invalid_domain() -> None:
    assert exact_decimal("0.42") == Decimal("0.42")
    with pytest.raises(NumericDomainError) as caught:
        exact_decimal(0.42)
    assert caught.value.reason_code is ReasonCode.FLOAT_DECIMAL_CONTAMINATION
    with pytest.raises(NumericDomainError) as caught:
        exact_decimal("NaN")
    assert caught.value.reason_code is ReasonCode.NONFINITE_NUMERIC_INPUT
    with pytest.raises(NumericDomainError):
        compute_math_01_binary_implied_probability("1.01", "1.00")
    with pytest.raises(NumericDomainError):
        compute_math_03_orderbook_midpoint(
            "0.4",
            "0.5",
            stale=1,  # type: ignore[arg-type]
        )
    with pytest.raises(NumericDomainError):
        compute_math_06_binary_contract_expected_net_cash(
            "1",
            "0.5",
            "1",
            "0",
            "-0.01",
            "0",
            "0",
            "0",
        )
    with pytest.raises(NumericDomainError) as caught:
        compute_math_06_binary_contract_expected_net_cash(
            "1",
            0.5,
            "1",
            "0",
            "0",
            "0",
            "0",
            "0",
        )
    assert caught.value.reason_code is ReasonCode.FLOAT_DECIMAL_CONTAMINATION
    assert compute_math_08_brier_score(0.7, 1) == pytest.approx(0.09)
    with pytest.raises(NumericDomainError):
        compute_math_08_brier_score(float("nan"), 1)
    with pytest.raises(NumericDomainError):
        compute_math_08_brier_score(0.7, True)
