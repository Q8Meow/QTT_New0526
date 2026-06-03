"""Build PR162D quantum problem model and local smoke records."""

from __future__ import annotations

from typing import Any

from ..deterministic_id import deterministic_id
from .classical_baseline_comparator import comparator_record
from .coefficient_validator import flatten_qubo_coefficients, validate_numeric_coefficients
from .constraint_feasibility_checker import check_linear_constraint
from .local_exact_ising_solver import solve_ising_exact
from .local_exact_qubo_solver import solve_qubo_exact
from .objective_value_calculator import ising_objective_value, qubo_objective_value
from .penalty_validator import penalty_validation_record
from .quantum_execution_result_envelope import quantum_execution_result_envelope


def quantum_problem_model_records() -> list[dict[str, Any]]:
    qubo_q = [[-1.0, -0.25], [-0.25, -0.5]]
    ising_h = [0.2, -0.4]
    ising_j = [(0, 1, 0.15)]
    return [
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-QUBO-MARKET-BUNDLE-001",
            "problem_model_type": "QUBO",
            "quantum_execution_mode": "QUANTUM_LOCAL_EXACT_SMOKE",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-QUBO_OBJECTIVE_XTQX"],
            "objective_expression": "x^T Q x + c",
            "objective_coefficients": {"Q": qubo_q, "constant_offset": 0.0},
            "constraints": [{"name": "budget_cap", "coefficients": [1.0, 1.0], "sense": "<=", "rhs": 1.0}],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-ISING-RISK-BUDGET-001",
            "problem_model_type": "ISING",
            "quantum_execution_mode": "QUANTUM_LOCAL_EXACT_SMOKE",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-ISING_ENERGY"],
            "objective_expression": "sum_i h_i s_i + sum_ij J_ij s_i s_j",
            "objective_coefficients": {"h": ising_h, "J": ising_j, "constant_offset": 0.0},
            "constraints": [],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-BQM-PARAMETER-STACK-001",
            "problem_model_type": "BQM",
            "quantum_execution_mode": "QUANTUM_DESCRIPTOR_ONLY",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-BQM_ENERGY"],
            "objective_expression": "linear + quadratic binary energy",
            "objective_coefficients": {"linear": [-0.4, -0.2], "quadratic": [(0, 1, 0.1)], "offset": 0.0},
            "constraints": [],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-CQM-EXPOSURE-001",
            "problem_model_type": "CQM",
            "quantum_execution_mode": "QUANTUM_DESCRIPTOR_ONLY",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-CQM_OBJECTIVE_CONSTRAINTS"],
            "objective_expression": "objective + lambda * constraint_violation^2",
            "objective_coefficients": {"linear": [-0.3, -0.1], "penalty_lambda": 3.0},
            "constraints": [{"name": "max_exposure", "coefficients": [1.0, 2.0], "sense": "<=", "rhs": 2.0}],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-QAOA-DESCRIPTOR-001",
            "problem_model_type": "QAOA_DESCRIPTOR",
            "quantum_execution_mode": "QUANTUM_PROVIDER_DRY_RUN",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-QAOA_HAMILTONIAN_MAPPING_CANDIDATE"],
            "objective_expression": "QUBO to Ising Hamiltonian descriptor",
            "objective_coefficients": {"source_problem_ref": "PR162D-QUANTUM-PROBLEM-QUBO-MARKET-BUNDLE-001", "reps": 1},
            "constraints": [],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-VQE-DESCRIPTOR-001",
            "problem_model_type": "VQE_DESCRIPTOR",
            "quantum_execution_mode": "QUANTUM_PROVIDER_DRY_RUN",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-VQE_OBJECTIVE_CANDIDATE"],
            "objective_expression": "sum c_i <H_i>",
            "objective_coefficients": {"hamiltonian_terms": [1.0, 2.0], "expectation_values": [0.5, 0.25]},
            "constraints": [],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
        {
            "problem_model_id": "PR162D-QUANTUM-PROBLEM-ANNEALING-DESCRIPTOR-001",
            "problem_model_type": "ANNEALING_DESCRIPTOR",
            "quantum_execution_mode": "QUANTUM_PROVIDER_DRY_RUN",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "formula_refs": ["PR162B-FORMULA-ANNEALING_BQM_CQM_CANDIDATE"],
            "objective_expression": "annealing BQM/CQM descriptor",
            "objective_coefficients": {"source_problem_ref": "PR162D-QUANTUM-PROBLEM-BQM-PARAMETER-STACK-001", "reads": 100},
            "constraints": [],
            "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
            "live_order_authority": False,
        },
    ]


def quantum_smoke_execution_records(problem_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for model in problem_models:
        if model["problem_model_type"] == "QUBO":
            q = model["objective_coefficients"]["Q"]
            result = solve_qubo_exact(q, max_variables=12)
            direct_value = qubo_objective_value(result["best_assignment"], q)
            result["objective_value_calculator_match_flag"] = direct_value == result["best_objective_value"]
            constraint = model["constraints"][0]
            result["constraint_feasibility"] = check_linear_constraint(
                result["best_assignment"],
                constraint["coefficients"],
                constraint["sense"],
                constraint["rhs"],
            )
            result["coefficient_validation"] = validate_numeric_coefficients(flatten_qubo_coefficients(q))
            result["penalty_validation"] = penalty_validation_record(
                result["constraint_feasibility"]["violation"],
                10.0,
            )
        elif model["problem_model_type"] == "ISING":
            coefficients = model["objective_coefficients"]
            result = solve_ising_exact(coefficients["h"], coefficients["J"], max_variables=12)
            direct_value = ising_objective_value(
                result["best_assignment"],
                coefficients["h"],
                coefficients["J"],
            )
            result["objective_value_calculator_match_flag"] = direct_value == result["best_objective_value"]
            result["coefficient_validation"] = validate_numeric_coefficients(coefficients["h"])
        else:
            continue
        smoke_id = deterministic_id("PR162D-QUANTUM-SMOKE", model["problem_model_id"])
        envelope = quantum_execution_result_envelope(smoke_id, model["problem_model_id"], result)
        envelope.update(
            {
                "qku_refs": model["qku_refs"],
                "formula_refs": model["formula_refs"],
                "problem_model_type": model["problem_model_type"],
                "quantum_execution_mode": "QUANTUM_LOCAL_EXACT_SMOKE",
            }
        )
        records.append(envelope)
    return records


def comparator_records(smoke_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for smoke in smoke_records:
        result = smoke["result"]
        value = float(result["best_objective_value"])
        records.append(
            comparator_record(
                deterministic_id("PR162D-QUANTUM-COMPARATOR", smoke["quantum_smoke_execution_id"]),
                smoke["quantum_smoke_execution_id"],
                value,
                value,
            )
        )
    return records
