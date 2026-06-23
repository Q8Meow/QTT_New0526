from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_quantum_rank_has_variables_coefficients_constraints_and_fallback() -> None:
    assert_rank3_valid()
    qrows = rows("q_rank")
    assert all(row["binary_variable_id"] and row["linear_coefficient_refs"] and row["constraint_refs"] for row in qrows)
    assert all(row["classical_comparator_exists"] and row["quantum_backend_execution_flag"] is False for row in qrows)
