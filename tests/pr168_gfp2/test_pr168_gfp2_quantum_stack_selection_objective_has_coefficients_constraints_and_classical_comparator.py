from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_quantum_stack_selection_objective_has_coefficients_constraints_and_classical_comparator() -> None:
    row = load("PR168_GFP2_QuantumPortfolioStackSelectionObjectiveSeed.report.json")[0]
    assert row["decision_variables"]
    assert row["constraints"]
    assert row["classical_comparator_exists"] is True
    assert row["backend_execution_flag"] is False
