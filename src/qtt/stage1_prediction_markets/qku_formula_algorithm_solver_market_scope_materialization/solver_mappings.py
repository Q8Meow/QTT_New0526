"""Solver mapping registry generation for PR162B."""

from __future__ import annotations

from typing import Any

from . import constants as c


def solver_mapping_records(
    qkus: list[dict[str, Any]],
    formula_by_name: dict[str, str],
    proofs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    proof_refs_by_qku = {record["qku_id"]: record["binding_proof_id"] for record in proofs if record["qku_id"] != "ALL_QKUS"}
    records: list[dict[str, Any]] = []
    for qku in qkus:
        qku_type = str(qku.get("qku_type") or "")
        subclass = str(qku.get("qku_quantum_subclass") or "")
        if qku_type not in {"OPTIMIZER_SETTING_QKU", "ALGORITHM_QKU", "FORMULA_QKU", "ATOMICROW_QKU"} and not subclass:
            continue
        if not subclass and qku_type != "OPTIMIZER_SETTING_QKU":
            continue
        family, representation, variable_type, constraint_type, formula_refs = _solver_family(subclass, formula_by_name)
        records.append(
            {
                "solver_mapping_id": f"PR162B-SOLVER-MAPPING-{len(records)+1:05d}",
                "qku_id": qku["qku_id"],
                "formula_refs": formula_refs,
                "objective_refs": formula_refs[:1],
                "constraint_refs": [
                    formula_by_name.get("binary penalty constraint lambda(Ax-b)^2", "")
                ],
                "algorithm_refs": [
                    "PR162B-ALGORITHM-QUBO_INPUT_ASSEMBLY_ALGORITHM"
                    if "QUBO" in family
                    else "PR162B-ALGORITHM-ISING_INPUT_ASSEMBLY_ALGORITHM"
                    if "ISING" in family
                    else "PR162B-ALGORITHM-EXACT_QUBO_SMOKE_ENUMERATION_ALGORITHM"
                ],
                "compatible_solver_family": family,
                "input_representation": representation,
                "variable_type": variable_type,
                "constraint_type": constraint_type,
                "requires_binary_variables": variable_type == "BINARY",
                "requires_integer_variables": False,
                "requires_continuous_variables": False,
                "supports_bounds": family
                in {"CLASSICAL_LINEAR_PROGRAM", "CLASSICAL_QUADRATIC_PROGRAM", "SCIPY_MINIMIZE_CANDIDATE"},
                "supports_linear_constraints": constraint_type in {"LINEAR", "PENALTY_LINEAR_QUADRATIC"},
                "supports_quadratic_constraints": constraint_type in {"QUADRATIC", "PENALTY_LINEAR_QUADRATIC"},
                "supports_penalty_constraints": True,
                "source_locator": _source_locator(family),
                "implementation_status": "IMPLEMENTED_SOLVER_INPUT_ASSEMBLY_ONLY"
                if "CANDIDATE" in family
                else "IMPLEMENTED_DETERMINISTIC_PYTHON",
                "smoke_execution_allowed_flag": family == "QUBO_EXACT_ENUMERATION_SMOKE",
                "evidence_execution_allowed_flag": False,
                "live_execution_allowed_flag": False,
                "binding_proof_refs": [proof_refs_by_qku[qku["qku_id"]]]
                if qku["qku_id"] in proof_refs_by_qku
                else [],
                "created_by_pr": c.PR_ID,
            }
        )
    return records


def _solver_family(subclass: str, formula_by_name: dict[str, str]) -> tuple[str, str, str, str, list[str]]:
    upper = subclass.upper()
    if "QUBO" in upper:
        return (
            "QUBO_EXACT_ENUMERATION_SMOKE",
            "QUBO_MATRIX",
            "BINARY",
            "PENALTY_LINEAR_QUADRATIC",
            [formula_by_name["QUBO objective x^T Q x"]],
        )
    if "ISING" in upper:
        return (
            "QISKIT_ISING_QAOA_CANDIDATE",
            "ISING_H_J",
            "SPIN",
            "PENALTY_LINEAR_QUADRATIC",
            [formula_by_name["Ising energy"]],
        )
    if "QAOA" in upper:
        return (
            "QISKIT_ISING_QAOA_CANDIDATE",
            "HAMILTONIAN_TERMS",
            "BINARY",
            "PENALTY_LINEAR_QUADRATIC",
            [formula_by_name["QAOA Hamiltonian mapping candidate"]],
        )
    if "VQE" in upper:
        return (
            "QISKIT_VQE_CANDIDATE",
            "HAMILTONIAN_EXPECTATION_TERMS",
            "CONTINUOUS_PARAMETER_VECTOR",
            "PENALTY_LINEAR_QUADRATIC",
            [formula_by_name["VQE objective candidate"]],
        )
    if "ANNEAL" in upper:
        return (
            "DWAVE_BQM_CANDIDATE",
            "BQM_OR_CQM",
            "BINARY",
            "PENALTY_LINEAR_QUADRATIC",
            [formula_by_name["annealing BQM/CQM candidate"]],
        )
    if "HYBRID" in upper:
        return (
            "HYBRID_SOLVER_CANDIDATE",
            "CLASSICAL_QUANTUM_COMPARATOR_OBJECTIVE",
            "BINARY",
            "PENALTY_LINEAR_QUADRATIC",
            [formula_by_name["hybrid classical-quantum comparator objective"]],
        )
    return (
        "CLASSICAL_VECTOR_FORMULA",
        "VECTOR_FORMULA_INPUT",
        "CONTINUOUS_PARAMETER_VECTOR",
        "NONE",
        [formula_by_name["mean_variance_objective"]],
    )


def _source_locator(family: str) -> str:
    if family.startswith("QISKIT"):
        return "https://qiskit-community.github.io/qiskit-optimization/"
    if family.startswith("DWAVE"):
        return "https://docs.dwavequantum.com/en/latest/concepts/models.html"
    if family.startswith("SCIPY"):
        return "https://docs.scipy.org/doc/scipy/reference/optimize.html"
    if family == "QUBO_EXACT_ENUMERATION_SMOKE":
        return "PR162B_LOCAL_TOY_EXACT_ENUMERATION_MAX_12_VARIABLES"
    return "PR162B_LOCAL_SOLVER_INPUT_ASSEMBLY_ONLY"
