from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    LinearTermV1,
    QuadraticVariableV1,
    compute_math_48_constrained_quadratic_model,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ObjectiveSense,
    VariableDomain,
)


def test_objective_sense_is_explicit_and_scale_is_preserved() -> None:
    variables = (
        QuadraticVariableV1("x", VariableDomain.BINARY, 0, 1),
        QuadraticVariableV1("y", VariableDomain.BINARY, 0, 1),
    )
    objective = (LinearTermV1("x", 2.5), LinearTermV1("y", -1.0))
    maximum = compute_math_48_constrained_quadratic_model(
        variables,
        objective,
        (),
        (),
        objective_sense=ObjectiveSense.MAXIMIZE,
    )
    minimum = compute_math_48_constrained_quadratic_model(
        variables,
        objective,
        (),
        (),
        objective_sense=ObjectiveSense.MINIMIZE,
    )
    assert maximum.objective == 2.5
    assert minimum.objective == -1.0
