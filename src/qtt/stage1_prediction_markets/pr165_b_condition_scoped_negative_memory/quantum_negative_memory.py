"""Quantum-specific PR165-B negative-memory rows."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def is_quantum_compatible(ctx: dict[str, Any]) -> bool:
    return ctx["quantum"].get("quantum_formulation_class") not in {None, "", "CLASSICAL_ONLY"}


def build_quantum_negative_memory_record(
    index: int,
    ctx: dict[str, Any],
    condition_id: str,
    combination_id: str,
    classification: dict[str, Any],
) -> dict[str, Any] | None:
    if not is_quantum_compatible(ctx) or classification["memory_classification"].startswith("POSITIVE"):
        return None
    quantum = ctx["quantum"]
    memory_classification = classification["memory_classification"]
    if memory_classification in {"QUANTUM_FORMULATION_WEAK", "QUANTUM_CLASSICAL_COMPARATOR_WEAK"}:
        attribution = memory_classification
    elif classification["reason_codes"][0] in {"PR165_B_COST_DEGRADATION", "PR165_B_LATENCY_DEGRADATION", "PR165_B_LIQUIDITY_DEGRADATION", "PR165_B_MODEL_RISK_DEGRADATION"}:
        attribution = "NON_QUANTUM_DEGRADATION_RECORDED"
    else:
        attribution = "CLASSICAL_BASELINE_PREFERRED_UNDER_CONDITION"
    return {
        "quantum_negative_memory_ref": ordinal_ref("PR165_B_QUANTUM_NEGATIVE_MEMORY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": memory_classification,
        "quantum_formulation_class": quantum.get("quantum_formulation_class"),
        "objective_function_materialized": quantum.get("objective_function_materialized", False),
        "variable_domain": quantum.get("variable_domain", ""),
        "binary_expansion_plan_ref": quantum.get("binary_expansion_plan_ref", ""),
        "constraint_count": quantum.get("constraint_count", 0),
        "penalty_model_ref": quantum.get("penalty_model_ref", quantum.get("quantum_formulation_materialization_ref", "")),
        "quadratic_matrix_or_equivalent_ref": quantum.get("quadratic_matrix_or_equivalent_ref", ""),
        "qubo_matrix_candidate_ref": quantum.get("qubo_matrix_candidate_ref", ""),
        "ising_hamiltonian_candidate_ref": quantum.get("ising_hamiltonian_candidate_ref", ""),
        "cqm_candidate_ref": quantum.get("cqm_candidate_ref", ""),
        "dqm_candidate_ref": quantum.get("dqm_candidate_ref", ""),
        "classical_comparator_ref": quantum.get("classical_comparator_ref", "PR165_CLASSICAL_COMPARATOR::LOCAL"),
        "quantum_failure_attribution": attribution,
        "quantum_repair_route": "QUANTUM_ROUTE_RETEST_AFTER_FORMULATION_REPAIR" if "QUANTUM" in attribution else "CLASSICAL_BASELINE_PREFERRED_UNDER_CONDITION",
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "validation_status": "PASS",
    }
