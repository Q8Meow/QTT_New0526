from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.quantum_objectives import (
    build_bqm_objective,
    build_cqm_objective,
    build_dqm_objective,
    build_ising_objective,
    build_quadprogram_objective,
    build_qubo_objective,
    compute_classical_fallback_solution,
    normalize_coefficients,
    quantum_objective_receipt,
)


def test_qubo_bqm_and_ising_objectives_preserve_coefficients():
    qubo = build_qubo_objective({"x0": 0}, {"x0": -0.1}, {"x0*x1": 0.2}, offset=0.3)
    bqm = build_bqm_objective({"x0": 0}, {"x0": -0.1}, {"x0*x1": 0.2}, offset=0.3)
    ising = build_ising_objective({"s0": 0}, {"s0": -1.0}, {"s0*s1": 0.5}, offset=0.2)

    assert qubo["objective_family"] == "QUBO_OBJECTIVE"
    assert bqm["objective_family"] == "BQM_OBJECTIVE"
    assert ising["objective_family"] == "ISING_OBJECTIVE"
    assert qubo["quadratic_coefficients"]["x0*x1"] == 0.2
    assert quantum_objective_receipt(qubo)["backend_execution_allowed"] is False
    assert quantum_objective_receipt(qubo)["quantum_advantage_claim"] is False


def test_cqm_dqm_and_quadprogram_objectives_include_constraints_or_cases():
    constraints = [{"constraint_id": "budget", "coefficients": {"x0": 1}, "sense": "<=", "rhs": 1}]
    cqm = build_cqm_objective({"x0": 0}, {"x0": -0.1}, {}, constraints)
    dqm = build_dqm_objective({"venue": ["a", "b"]}, {"venue:a": 0.1}, {"venue:a|venue:b": 0.2})
    qp = build_quadprogram_objective({"x0": 0}, "minimize", {"x0": -0.1}, {}, constraints)

    assert cqm["constraints"] == constraints
    assert dqm["linear_case_coefficients"]["venue:a"] == 0.1
    assert qp["objective_sense"] == "minimize"


def test_normalize_coefficients_and_classical_fallback_solution():
    normalized = normalize_coefficients({"x0": 4.0}, {"x0*x1": -2.0}, max_abs_coefficient=1.0)
    assert normalized["linear_coefficients"]["x0"] == 1.0
    result = compute_classical_fallback_solution({"x0": -1.0, "x1": 0.5, "x0*x1": 2.0}, [], deterministic_limit=2)
    assert result["solution"]["x0"] == 1
