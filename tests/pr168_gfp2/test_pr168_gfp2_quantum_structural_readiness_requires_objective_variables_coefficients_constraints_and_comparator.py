from tests.pr168_gfp2.pr168_gfp2_test_support import validate_quantum


def test_quantum_structural_readiness_requires_objective_variables_coefficients_constraints_and_comparator() -> None:
    validate_quantum()
