from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (
    QuantumMappingViewV1,
    QuantumModelKind,
)


def test_problem_shape_is_an_explicit_closed_enum() -> None:
    assert tuple(QuantumModelKind) == (
        QuantumModelKind.QUBO,
        QuantumModelKind.BQM,
        QuantumModelKind.ISING,
        QuantumModelKind.CQM,
        QuantumModelKind.DQM,
        QuantumModelKind.QUADRATIC_PROGRAM,
    )
    view = QuantumMappingViewV1(
        "row-1",
        QuantumModelKind.CQM,
        "docs/master_plan/generated/PR162E_Q_CQMRecipe.report.json",
        "pr162e_q_cqm_recipe.schema.json",
    )
    assert view.model_kind is QuantumModelKind.CQM
    assert not view.backend_execution_allowed
