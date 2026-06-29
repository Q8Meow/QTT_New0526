from ._helpers import assert_rows_have_contract


def test_quantum_grid_encoding_has_structure_without_execution_or_advantage_claims() -> None:
    q_grid = assert_rows_have_contract("q_grid.jsonl")
    q_constraints = assert_rows_have_contract("q_constraints.jsonl")
    q_interp = assert_rows_have_contract("q_interp.jsonl")
    fallback = assert_rows_have_contract("classic_fallback.jsonl")

    assert all(row["binary_side_variables"] for row in q_grid)
    assert all(row["variable_count"] > 0 for row in q_grid)
    assert all(row["constraint_count"] > 0 for row in q_grid)
    assert all(row["future_qopt1_consumer_flag"] for row in q_grid)
    assert all(row["qopt_execution_flag"] is False for row in q_grid)
    assert all(row["constraints"] for row in q_constraints)
    assert all(row["interpret_back_map"] for row in q_interp)
    assert all(row["classical_optimizer_refs"] for row in fallback)
