from ._helpers import read_jsonl


def test_quantum_structural_readiness_has_objective_variables_constraints_and_fallback() -> None:
    rows = read_jsonl("q_obj.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["objective_terms"]
        assert row["linear_coefficients"]
        assert row["variable_domains"]
        assert row["constraint_terms"]
        assert row["interpret_back_map_ref"]
        assert row["classical_fallback_ref"]
        assert row["qopt_execution_flag"] is False
