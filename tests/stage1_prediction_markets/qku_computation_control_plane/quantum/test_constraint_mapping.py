import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    LinearTermV1,
    QuadraticConstraintV1,
    QuadraticTermV1,
    QuadraticVariableV1,
    compute_math_48_constrained_quadratic_model,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ObjectiveSense,
    VariableDomain,
)


def test_hard_constraint_is_enumerated_and_revalidated() -> None:
    variables = (
        QuadraticVariableV1("x", VariableDomain.BINARY, 0, 1),
        QuadraticVariableV1("y", VariableDomain.BINARY, 0, 1),
    )
    objective = (LinearTermV1("x", 1), LinearTermV1("y", 1))
    constraint = QuadraticConstraintV1(
        "x+y<=1",
        objective,
        (),
        "<=",
        1,
    )
    result = compute_math_48_constrained_quadratic_model(
        variables,
        objective,
        (),
        (constraint,),
        objective_sense=ObjectiveSense.MAXIMIZE,
    )
    assert result.feasible
    assert result.objective == 1
    assert sum(value for _name, value in result.assignment) <= 1
    assert result.label_crosswalk == (("x", 0), ("y", 1))

    malformed = QuadraticConstraintV1(
        "unknown",
        (LinearTermV1("z", 1),),
        (),
        "<=",
        1,
    )
    with pytest.raises(ValueError):
        compute_math_48_constrained_quadratic_model(
            variables,
            objective,
            (),
            (malformed,),
            objective_sense=ObjectiveSense.MAXIMIZE,
        )
    duplicate = QuadraticConstraintV1(
        "x+y<=1",
        objective,
        (),
        ">=",
        0,
    )
    with pytest.raises(ValueError):
        compute_math_48_constrained_quadratic_model(
            variables,
            objective,
            (),
            (constraint, duplicate),
            objective_sense=ObjectiveSense.MAXIMIZE,
        )
    real = (QuadraticVariableV1("r", VariableDomain.REAL, 1.0, 1.0),)
    with pytest.raises(ValueError):
        compute_math_48_constrained_quadratic_model(
            real,
            (),
            (QuadraticTermV1("r", "r", 1.0),),
            (),
            objective_sense=ObjectiveSense.MINIMIZE,
        )
