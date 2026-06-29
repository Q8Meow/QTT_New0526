from ._helpers import assert_rows_have_contract


def test_quantum_problem_has_coefficients_and_no_backend() -> None:
    row = assert_rows_have_contract("qstruct_problem.jsonl")[0]
    assert row["linear_coefficients"]
    assert row["constraint_matrix_or_constraint_terms"]
    assert row["quantum_backend_execution_flag"] is False

