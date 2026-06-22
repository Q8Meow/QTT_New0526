from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_quantum_structural_candidate_map_requires_objective_coefficients_constraints_and_classical_fallback() -> None:
    quantum_rows = rows("quantum_candidate_stack")
    assert quantum_rows
    assert all(row["binary_variable_id"] for row in quantum_rows)
    assert all(row["linear_coefficient_refs"] and row["quadratic_coefficient_refs"] for row in quantum_rows)
    assert all(row["constraint_refs"] for row in quantum_rows)
    assert all(row["classical_fallback_exists"] and row["classical_comparator_exists"] for row in quantum_rows)
