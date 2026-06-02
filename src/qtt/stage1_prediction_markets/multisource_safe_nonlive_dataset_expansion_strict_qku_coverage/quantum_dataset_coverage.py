"""PR162C quantum-forward dataset coverage records without backend execution."""

from __future__ import annotations

from typing import Any

from . import constants as c


def quantum_feature_coverage_records(proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-QUANTUM-FEATURE-COVERAGE-{proof['qku_id']}",
            "qku_id": proof["qku_id"],
            "data_requirement_id": proof["data_requirement_id"],
            "quantum_feature_dataset_required_flag": proof["quantum_feature_dataset_required_flag"],
            "quantum_feature_dataset_available_flag": proof["quantum_feature_dataset_available_flag"],
            "strict_coverage_status": proof["strict_coverage_status"],
            "backend_execution_allowed_flag": False,
            "simulator_execution_allowed_flag": False,
            "blocker_code": proof["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for proof in proofs
        if proof["quantum_feature_dataset_required_flag"]
    ]


def qubo_ising_dataset_feature_records(proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-QUBO-ISING-DATASET-FEATURE-{proof['qku_id']}",
            "qku_id": proof["qku_id"],
            "dataset_ids": proof["dataset_ids"],
            "qubo_variables_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "ising_spins_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "bqm_variables_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "cqm_constraints_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "penalty_terms_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "objective_coefficients_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "constraint_matrices_covered_flag": proof["quantum_feature_dataset_available_flag"],
            "blocker_code": proof["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for proof in proofs
        if proof["quantum_feature_dataset_required_flag"]
    ]


def solver_input_assembly_coverage_records(solver_mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-QUANTUM-SOLVER-ASSEMBLY-{record['solver_mapping_id']}",
            "solver_mapping_ref": record["solver_mapping_id"],
            "input_representation": record.get("input_representation"),
            "implementation_status": record.get("implementation_status"),
            "solver_input_assembly_only_flag": True,
            "backend_execution_allowed_flag": False,
            "simulator_execution_allowed_flag": False,
            "created_by_pr": c.PR_ID,
        }
        for record in solver_mappings
    ]
