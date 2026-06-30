from ._helpers import rows


def test_quantum_structures_have_coefficients_constraints_and_no_backend() -> None:
    for filename in ("qproblem.jsonl", "qubo.jsonl", "bqm.jsonl", "cqm.jsonl", "quad_prog.jsonl", "ising_map.jsonl"):
        row = rows(filename)[0]
        assert row["linear_coefficients"]
        assert row["constraint_terms"]
        assert row["penalty_weight_numeric_values"]
        assert row["true_quantum_backend_execution_flag"] is False
        assert row["quantum_advantage_claim_flag"] is False
    assert rows("qobj_coeff.jsonl")
    assert rows("qconstraints.jsonl")
