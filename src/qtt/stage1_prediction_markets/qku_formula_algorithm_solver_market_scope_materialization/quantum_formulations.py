"""QUBO, Ising, BQM, CQM, QAOA, VQE, and hybrid toy formulations for PR162B."""

from __future__ import annotations

from itertools import product
from typing import Any


def validate_qubo_matrix(Q: list[list[float]] | tuple[tuple[float, ...], ...]) -> list[list[float]]:
    matrix = [[float(value) for value in row] for row in Q]
    if not matrix:
        raise ValueError("Q must not be empty")
    width = len(matrix)
    if any(len(row) != width for row in matrix):
        raise ValueError("Q must be square")
    return matrix


def qubo_energy(x: list[int] | tuple[int, ...], Q: list[list[float]] | tuple[tuple[float, ...], ...]) -> float:
    matrix = validate_qubo_matrix(Q)
    bits = [int(value) for value in x]
    if len(bits) != len(matrix):
        raise ValueError("x length must match Q dimension")
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("x must be binary")
    return sum(bits[i] * matrix[i][j] * bits[j] for i in range(len(bits)) for j in range(len(bits)))


def expanded_qubo_terms(Q: list[list[float]] | tuple[tuple[float, ...], ...]) -> list[dict[str, Any]]:
    matrix = validate_qubo_matrix(Q)
    terms: list[dict[str, Any]] = []
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value != 0.0:
                terms.append({"i": i, "j": j, "coefficient": value, "term": f"x_{i}*x_{j}"})
    return terms


def validate_ising_terms(
    h: list[float] | tuple[float, ...],
    J: dict[tuple[int, int], float] | list[tuple[int, int, float]],
) -> tuple[list[float], dict[tuple[int, int], float]]:
    fields = [float(value) for value in h]
    if not fields:
        raise ValueError("h must not be empty")
    couplers: dict[tuple[int, int], float] = {}
    items = J.items() if isinstance(J, dict) else [((i, j), value) for i, j, value in J]
    for key, value in items:
        i, j = key
        if i == j:
            raise ValueError("Ising coupler cannot be self-coupled")
        if i < 0 or j < 0 or i >= len(fields) or j >= len(fields):
            raise ValueError("Ising coupler index out of range")
        couplers[(int(i), int(j))] = float(value)
    return fields, couplers


def ising_energy(
    spins: list[int] | tuple[int, ...],
    h: list[float] | tuple[float, ...],
    J: dict[tuple[int, int], float] | list[tuple[int, int, float]],
) -> float:
    fields, couplers = validate_ising_terms(h, J)
    ss = [int(value) for value in spins]
    if len(ss) != len(fields):
        raise ValueError("spins length must match h length")
    if any(spin not in (-1, 1) for spin in ss):
        raise ValueError("spins must be -1 or 1")
    total = sum(field * spin for field, spin in zip(fields, ss, strict=True))
    total += sum(value * ss[i] * ss[j] for (i, j), value in couplers.items())
    return total


def bqm_energy(
    x: list[int],
    linear: list[float],
    quadratic: dict[tuple[int, int], float] | list[tuple[int, int, float]],
) -> float:
    bits = [int(value) for value in x]
    if len(bits) != len(linear):
        raise ValueError("x length must match linear terms")
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("x must be binary")
    total = sum(float(coef) * bit for coef, bit in zip(linear, bits, strict=True))
    items = quadratic.items() if isinstance(quadratic, dict) else [((i, j), value) for i, j, value in quadratic]
    for (i, j), coefficient in items:
        total += float(coefficient) * bits[i] * bits[j]
    return total


def binary_penalty_constraint(Ax_minus_b: float, lambda_penalty: float) -> float:
    penalty = float(lambda_penalty)
    if penalty < 0.0:
        raise ValueError("lambda_penalty must be non-negative")
    return penalty * float(Ax_minus_b) ** 2


def cqm_objective_and_constraints(
    objective_value: float,
    constraint_violations: list[float] | tuple[float, ...],
    penalty_lambda: float,
) -> float:
    return float(objective_value) + sum(
        binary_penalty_constraint(value, penalty_lambda) for value in constraint_violations
    )


def exact_qubo_smoke_solve(Q: list[list[float]], max_variables: int = 12) -> dict[str, Any]:
    matrix = validate_qubo_matrix(Q)
    n = len(matrix)
    if n > int(max_variables):
        raise ValueError("Q dimension exceeds max_variables smoke cap")
    best_x: list[int] | None = None
    best_energy: float | None = None
    for candidate in product((0, 1), repeat=n):
        energy = qubo_energy(list(candidate), matrix)
        if best_energy is None or energy < best_energy:
            best_energy = energy
            best_x = list(candidate)
    return {
        "best_x": best_x,
        "best_energy": best_energy,
        "status": "SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
        "variable_count": n,
    }


def qubo_portfolio_selection_objective(
    expected_returns: list[float],
    risk_matrix: list[list[float]],
    risk_aversion: float,
) -> list[list[float]]:
    matrix = validate_qubo_matrix(risk_matrix)
    if len(expected_returns) != len(matrix):
        raise ValueError("expected_returns length must match risk_matrix")
    return [
        [
            float(risk_aversion) * matrix[i][j] - (float(expected_returns[i]) if i == j else 0.0)
            for j in range(len(matrix))
        ]
        for i in range(len(matrix))
    ]


def qubo_prediction_market_position_selection_objective(
    edges: list[float],
    risk_penalties: list[float],
) -> list[list[float]]:
    if len(edges) != len(risk_penalties):
        raise ValueError("edges and risk_penalties must have equal length")
    return [
        [
            float(risk_penalties[i]) - float(edges[i]) if i == j else 0.0
            for j in range(len(edges))
        ]
        for i in range(len(edges))
    ]


def qubo_market_bundle_selection_objective(scores: list[float]) -> list[list[float]]:
    return [[-float(score) if i == j else 0.0 for j in range(len(scores))] for i, score in enumerate(scores)]


def qubo_parameter_stack_selection_objective(scores: list[float], penalties: list[float]) -> list[list[float]]:
    if len(scores) != len(penalties):
        raise ValueError("scores and penalties must have equal length")
    return [[float(penalties[i]) - float(scores[i]) if i == j else 0.0 for j in range(len(scores))] for i in range(len(scores))]


def qubo_risk_budget_objective(exposures: list[float], budget: float, penalty_lambda: float) -> list[list[float]]:
    budget_value = float(budget)
    if budget_value <= 0.0:
        raise ValueError("budget must be positive")
    penalty = float(penalty_lambda)
    return [
        [
            penalty * float(exposures[i]) * float(exposures[j]) / budget_value
            for j in range(len(exposures))
        ]
        for i in range(len(exposures))
    ]


def qaoa_hamiltonian_mapping_candidate(Q: list[list[float]]) -> dict[str, Any]:
    matrix = validate_qubo_matrix(Q)
    return {
        "hamiltonian_family": "QAOA_QUBO_TO_ISING_CANDIDATE",
        "term_count": len(expanded_qubo_terms(matrix)),
        "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    }


def vqe_objective_candidate(hamiltonian_terms: list[float], expectation_values: list[float]) -> float:
    if len(hamiltonian_terms) != len(expectation_values):
        raise ValueError("hamiltonian_terms and expectation_values must have equal length")
    return sum(float(term) * float(expectation) for term, expectation in zip(hamiltonian_terms, expectation_values, strict=True))


def annealing_bqm_cqm_candidate(Q: list[list[float]]) -> dict[str, Any]:
    matrix = validate_qubo_matrix(Q)
    return {
        "input_representation": "BQM_OR_CQM_CANDIDATE",
        "variable_count": len(matrix),
        "term_count": len(expanded_qubo_terms(matrix)),
        "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    }


def hybrid_classical_quantum_comparator_objective(classical_score: float, quantum_candidate_score: float) -> float:
    return float(quantum_candidate_score) - float(classical_score)


def assemble_qubo_input(Q: list[list[float]]) -> dict[str, Any]:
    matrix = validate_qubo_matrix(Q)
    return {
        "input_representation": "QUBO_MATRIX",
        "variable_type": "BINARY",
        "variable_count": len(matrix),
        "Q": matrix,
        "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    }


def assemble_ising_input(
    h: list[float],
    J: dict[tuple[int, int], float] | list[tuple[int, int, float]],
) -> dict[str, Any]:
    fields, couplers = validate_ising_terms(h, J)
    return {
        "input_representation": "ISING_H_J",
        "variable_type": "SPIN",
        "variable_count": len(fields),
        "h": fields,
        "J": {f"{i},{j}": value for (i, j), value in sorted(couplers.items())},
        "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    }
