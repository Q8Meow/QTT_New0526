from decimal import Decimal
from itertools import permutations

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    canonical_probability_decimal,
    decimal_context_v1,
    exact_decimal,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    QuantityAndFrictionTermsV1,
    compute_math_01_binary_implied_probability,
    compute_math_03_orderbook_midpoint,
    compute_math_06_binary_contract_expected_net_cash,
    compute_math_07_multi_outcome_expected_net_cash,
    compute_math_08_brier_score,
    normalize_probability_vector,
)


def _terms(quantity: str = "1") -> QuantityAndFrictionTermsV1:
    return QuantityAndFrictionTermsV1(
        Decimal(quantity),
        Decimal("0.02"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
    )


def test_general_decimal_boundary_remains_exact_while_probability_is_centralized() -> None:
    assert exact_decimal("0.42") == Decimal("0.42")
    context = decimal_context_v1()
    accepted_text = f"1e{context.Emax}"
    overflow_text = f"1e{context.Emax + 1}"
    assert exact_decimal(accepted_text) == Decimal(accepted_text)
    with pytest.raises(NumericDomainError) as caught:
        exact_decimal(overflow_text)
    assert caught.value.reason_code is ReasonCode.INVALID_NUMERIC_INPUT

    with pytest.raises(NumericDomainError) as caught:
        exact_decimal(0.42)
    assert caught.value.reason_code is ReasonCode.FLOAT_DECIMAL_CONTAMINATION

    class NumericLookingObject:
        def __str__(self) -> str:
            return "0.5"

    for unsupported in (
        (0, (1, 2, 3), -2),
        [0, (1, 2, 3), -2],
        NumericLookingObject(),
    ):
        with pytest.raises(NumericDomainError) as caught:
            exact_decimal(unsupported)  # type: ignore[arg-type]
        assert caught.value.reason_code is ReasonCode.INVALID_NUMERIC_INPUT

    assert canonical_probability_decimal(0.42) == Decimal("0.42")
    assert canonical_probability_decimal("0.42") == Decimal("0.42")
    for value in (True, float("nan"), float("inf"), -0.01, 1.01):
        with pytest.raises(NumericDomainError):
            canonical_probability_decimal(value)  # type: ignore[arg-type]
    with pytest.raises(NumericDomainError):
        compute_math_01_binary_implied_probability("1.01", "1.00")
    with pytest.raises(NumericDomainError):
        compute_math_03_orderbook_midpoint(
            "0.4",
            "0.5",
            stale=1,  # type: ignore[arg-type]
        )
    assert compute_math_08_brier_score(0.7, 1) == pytest.approx(0.09)


def test_math_06_float_surface_boundaries_equivalence_and_quantity_linearity() -> None:
    common = ("0.55", "-0.45", "0", "0", "0", "0")
    as_float = compute_math_06_binary_contract_expected_net_cash(
        "1",
        0.6,
        *common,
    )
    as_string = compute_math_06_binary_contract_expected_net_cash(
        "1",
        "0.6",
        *common,
    )
    assert as_float == as_string == Decimal("0.15")
    assert compute_math_06_binary_contract_expected_net_cash(
        "1",
        0.0,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    ) == Decimal("-1")
    assert compute_math_06_binary_contract_expected_net_cash(
        "1",
        1.0,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    ) == Decimal("2")
    one = compute_math_06_binary_contract_expected_net_cash(
        "1",
        0.6,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    )
    two = compute_math_06_binary_contract_expected_net_cash(
        "2",
        0.6,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    )
    assert two == 2 * one
    for value in (True, float("nan"), float("inf"), -0.01, 1.01):
        with pytest.raises(NumericDomainError):
            compute_math_06_binary_contract_expected_net_cash(
                "1",
                value,
                "1",
                "0",
                "0",
                "0",
                "0",
                "0",
            )


def test_math_07_receipt_normalization_equivalence_and_permutation_invariance() -> None:
    receipt = normalize_probability_vector((0.1, 0.2, 0.7000000000000001))
    assert receipt.normalization_applied
    assert receipt.original_sum == Decimal("1.0")
    assert receipt.tolerance > 0
    assert receipt.canonical_decimal_vector == (
        Decimal("0.1"),
        Decimal("0.2"),
        Decimal("0.7000000000000001"),
    )
    assert sum(receipt.normalized_decimal_vector, Decimal(0)) == Decimal(1)

    float_result = compute_math_07_multi_outcome_expected_net_cash(
        (0.2, 0.3, 0.5),
        ("1.0", "-0.2", "0.1"),
        _terms(),
    )
    string_result = compute_math_07_multi_outcome_expected_net_cash(
        ("0.2", "0.3", "0.5"),
        ("1.0", "-0.2", "0.1"),
        _terms(),
    )
    assert float_result == string_result == Decimal("0.17")
    paired = ((0.2, "1.0"), (0.3, "-0.2"), (0.5, "0.1"))
    for permuted in permutations(paired):
        assert compute_math_07_multi_outcome_expected_net_cash(
            tuple(item[0] for item in permuted),
            tuple(item[1] for item in permuted),
            _terms(),
        ) == float_result
    assert compute_math_07_multi_outcome_expected_net_cash(
        (1.0, 0.0),
        ("2", "-9"),
        QuantityAndFrictionTermsV1(
            Decimal("1"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
    ) == Decimal("2")


def test_math_07_rejects_nonfinite_outside_tolerance_and_mismatch() -> None:
    invalid = (
        ((float("nan"), 0.0), ("1", "2")),
        ((float("inf"), 0.0), ("1", "2")),
        ((0.4, 0.4), ("1", "2")),
        ((0.5, 0.5), ("1",)),
    )
    for probabilities, payoffs in invalid:
        with pytest.raises(NumericDomainError):
            compute_math_07_multi_outcome_expected_net_cash(
                probabilities,
                payoffs,
                _terms(),
            )
