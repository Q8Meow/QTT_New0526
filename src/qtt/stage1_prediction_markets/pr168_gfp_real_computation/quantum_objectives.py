"""Quantum-objective and deterministic fallback formulas for PR168-GFP."""

from __future__ import annotations

from itertools import product


def build_qubo_objective(
    variable_map: dict[str, int],
    linear_coefficients: dict[str, float],
    quadratic_coefficients: dict[str, float],
    offset: float = 0.0,
) -> dict[str, object]:
    return {
        "objective_family": "QUBO_OBJECTIVE",
        "variable_map": dict(variable_map),
        "linear_coefficients": {str(k): float(v) for k, v in linear_coefficients.items()},
        "quadratic_coefficients": {str(k): float(v) for k, v in quadratic_coefficients.items()},
        "offset": float(offset),
        "variable_domain": "BINARY",
    }


def build_bqm_objective(
    variable_map: dict[str, int],
    linear_coefficients: dict[str, float],
    quadratic_coefficients: dict[str, float],
    offset: float = 0.0,
) -> dict[str, object]:
    objective = build_qubo_objective(variable_map, linear_coefficients, quadratic_coefficients, offset)
    objective["objective_family"] = "BQM_OBJECTIVE"
    return objective


def build_ising_objective(
    spin_map: dict[str, int],
    h_coefficients: dict[str, float],
    j_coefficients: dict[str, float],
    offset: float = 0.0,
) -> dict[str, object]:
    return {
        "objective_family": "ISING_OBJECTIVE",
        "spin_map": dict(spin_map),
        "h_coefficients": {str(k): float(v) for k, v in h_coefficients.items()},
        "j_coefficients": {str(k): float(v) for k, v in j_coefficients.items()},
        "offset": float(offset),
        "variable_domain": "SPIN",
    }


def build_cqm_objective(
    variable_map: dict[str, int],
    linear_coefficients: dict[str, float],
    quadratic_coefficients: dict[str, float],
    constraints: list[dict[str, object]],
    offset: float = 0.0,
) -> dict[str, object]:
    objective = build_qubo_objective(variable_map, linear_coefficients, quadratic_coefficients, offset)
    objective["objective_family"] = "CQM_OBJECTIVE"
    objective["constraints"] = list(constraints)
    return objective


def build_dqm_objective(
    discrete_variable_map: dict[str, list[str]],
    linear_case_coefficients: dict[str, float],
    quadratic_case_coefficients: dict[str, float],
    offset: float = 0.0,
) -> dict[str, object]:
    return {
        "objective_family": "DQM_OBJECTIVE",
        "discrete_variable_map": dict(discrete_variable_map),
        "linear_case_coefficients": {str(k): float(v) for k, v in linear_case_coefficients.items()},
        "quadratic_case_coefficients": {str(k): float(v) for k, v in quadratic_case_coefficients.items()},
        "offset": float(offset),
    }


def build_quadprogram_objective(
    variable_map: dict[str, int],
    objective_sense: str,
    linear_coefficients: dict[str, float],
    quadratic_coefficients: dict[str, float],
    constraints: list[dict[str, object]],
    offset: float = 0.0,
) -> dict[str, object]:
    return {
        "objective_family": "QUADPROGRAM_OBJECTIVE",
        "variable_map": dict(variable_map),
        "objective_sense": objective_sense,
        "linear_coefficients": {str(k): float(v) for k, v in linear_coefficients.items()},
        "quadratic_coefficients": {str(k): float(v) for k, v in quadratic_coefficients.items()},
        "constraints": list(constraints),
        "offset": float(offset),
    }


def add_constraint_penalties(objective_terms: dict[str, float], constraints: list[dict[str, object]], penalty_scale: float) -> dict[str, float]:
    adjusted = {str(k): float(v) for k, v in objective_terms.items()}
    for constraint in constraints:
        key = str(constraint.get("penalty_key", constraint.get("constraint_id", "constraint_penalty")))
        violation = float(constraint.get("violation", 0.0))
        adjusted[key] = adjusted.get(key, 0.0) + float(penalty_scale) * violation * violation
    return adjusted


def normalize_coefficients(
    linear_coefficients: dict[str, float],
    quadratic_coefficients: dict[str, float],
    max_abs_coefficient: float,
) -> dict[str, dict[str, float]]:
    current_max = max(
        [abs(float(v)) for v in linear_coefficients.values()] + [abs(float(v)) for v in quadratic_coefficients.values()] + [1e-12]
    )
    scale = min(1.0, float(max_abs_coefficient) / current_max)
    return {
        "linear_coefficients": {str(k): float(v) * scale for k, v in linear_coefficients.items()},
        "quadratic_coefficients": {str(k): float(v) * scale for k, v in quadratic_coefficients.items()},
    }


def interpret_binary_solution_back(solution_vector: dict[str, int], variable_map: dict[str, str]) -> dict[str, int]:
    return {str(variable_map.get(name, name)): int(value) for name, value in solution_vector.items()}


def compute_classical_fallback_solution(
    objective_terms: dict[str, float],
    constraints: list[dict[str, object]] | None,
    deterministic_limit: int,
) -> dict[str, object]:
    variables = sorted({term.split("*")[0] for term in objective_terms if "*" not in term})
    variables = variables[: max(0, int(deterministic_limit))]
    best_solution: dict[str, int] | None = None
    best_value: float | None = None
    for values in product([0, 1], repeat=len(variables)):
        solution = dict(zip(variables, values))
        if constraints and not _feasible(solution, constraints):
            continue
        value = _objective_value(solution, objective_terms)
        if best_value is None or value < best_value:
            best_value = value
            best_solution = solution
    return {"solution": best_solution or {}, "objective_value": 0.0 if best_value is None else best_value}


def quantum_objective_receipt(objective: dict[str, object]) -> dict[str, object]:
    return {
        "quantum_model_family": objective.get("objective_family"),
        "backend_execution_allowed": False,
        "quantum_advantage_claim": False,
        "objective_terms_present": bool(objective),
    }


def _objective_value(solution: dict[str, int], objective_terms: dict[str, float]) -> float:
    total = 0.0
    for term, coefficient in objective_terms.items():
        names = term.split("*")
        product_value = 1
        for name in names:
            product_value *= int(solution.get(name, 0))
        total += float(coefficient) * product_value
    return total


def _feasible(solution: dict[str, int], constraints: list[dict[str, object]]) -> bool:
    for constraint in constraints:
        coefficients = constraint.get("coefficients", {})
        lhs = sum(float(coefficients.get(name, 0.0)) * value for name, value in solution.items())
        sense = constraint.get("sense", "<=")
        rhs = float(constraint.get("rhs", 0.0))
        if sense == "<=" and lhs > rhs:
            return False
        if sense == ">=" and lhs < rhs:
            return False
        if sense == "==" and abs(lhs - rhs) > 1e-12:
            return False
    return True
