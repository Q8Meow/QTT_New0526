#!/usr/bin/env python3
"""Quantum structural readiness without backend execution for PR168-RP."""

from __future__ import annotations

from typing import Any


QUANTUM_FORMULA_IDS = {
    "PR168_GFP_FORMULA_QUBO_OBJECTIVE",
    "PR168_GFP_FORMULA_BQM_OBJECTIVE",
    "PR168_GFP_FORMULA_ISING_OBJECTIVE",
    "PR168_GFP_FORMULA_CQM_OBJECTIVE",
    "PR168_GFP_FORMULA_DQM_OBJECTIVE",
    "PR168_GFP_FORMULA_QUADPROGRAM_OBJECTIVE",
}


def compute_quantum_structural_readiness(assignment: dict[str, Any]) -> dict[str, Any]:
    formula_ids = set(assignment.get("formula_ids") or [])
    material = bool(formula_ids & QUANTUM_FORMULA_IDS)
    missing = []
    if material:
        missing = [
            "objective_expression",
            "variable_domain_map",
            "coefficient_map",
            "constraint_map_if_required",
            "penalty_scale",
            "interpret_back_map",
            "classical_fallback_objective_inputs",
        ]
    return {
        "quantum_materiality_flag": material,
        "quantum_structural_readiness": "QUANTUM_COEFFICIENT_MAP_INPUT_GAP" if material else "NOT_QUANTUM_MATERIAL",
        "objective_expression_verified": material,
        "variable_map_verified": bool(assignment.get("formula_ids")),
        "variable_domain_map_verified": False if material else None,
        "coefficient_map_verified": False if material else None,
        "linear_coefficients_verified": False if material else None,
        "quadratic_coefficients_verified": False if material else None,
        "offset_verified": False if material else None,
        "constraint_map_verified": False if material else None,
        "penalty_scale_verified": False if material else None,
        "interpret_back_map_verified": False if material else None,
        "classical_fallback_objective_verified": False if material else None,
        "strongest_classical_comparator_verified": False if material else None,
        "missing_quantum_inputs": missing,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "downstream_route": "PR168_RP_QuantumCoefficientMapInputGaps.report.json" if material else "PR168_RP_QuantumStructuralReadiness.report.json",
        "downstream_pr": "PR166-QC-R2" if material else "PR168-RANK",
    }
