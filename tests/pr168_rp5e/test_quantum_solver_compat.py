from ._helpers import read_jsonl


def test_quantum_solver_compat_contains_scale_counts_and_interpret_back_refs() -> None:
    rows = read_jsonl("q_solver.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["coefficient_scale_min"] <= row["coefficient_scale_max"]
        assert row["variable_count"] >= row["binary_variable_count"]
        assert row["constraint_count"] > 0
        assert row["interpret_back_map_ref"]
        assert row["solver_execution_allowed_in_rp5e_flag"] is False
