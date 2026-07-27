import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    DiscreteLinearBiasV1,
    DiscreteVariableV1,
    QuadraticVariableV1,
    compute_math_49_discrete_quadratic_model,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    VariableDomain,
)


def test_binary_and_discrete_encodings_are_exact_and_reversible() -> None:
    binary = QuadraticVariableV1("x", VariableDomain.BINARY, 0, 1)
    assert binary.values() == (0, 1)
    variables = (
        DiscreteVariableV1("a", ("A0", "A1")),
        DiscreteVariableV1("b", ("B0", "B1")),
    )
    result = compute_math_49_discrete_quadratic_model(
        variables,
        (
            DiscreteLinearBiasV1("a", "A0", 0),
            DiscreteLinearBiasV1("a", "A1", 1),
            DiscreteLinearBiasV1("b", "B0", 0),
            DiscreteLinearBiasV1("b", "B1", 1),
        ),
        (),
    )
    assert dict(result.assignment) == {"a": "A0", "b": "B0"}
    assert result.interpret_back_map == (
        ("a", ("A0", "A1")),
        ("b", ("B0", "B1")),
    )
    assert result.one_case_per_variable
    fixed_real = QuadraticVariableV1("fixed", VariableDomain.REAL, 1.5, 1.5)
    assert fixed_real.values() == (1.5,)
    with pytest.raises(NumericDomainError):
        QuadraticVariableV1("free", VariableDomain.REAL, 0.0, 1.0).values()
    with pytest.raises(NumericDomainError):
        DiscreteLinearBiasV1("a", "A0", float("nan"))
