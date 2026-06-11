"""Quantum mapping readiness and priority scoring without backend execution."""

from __future__ import annotations

from typing import Any

from .cost_model import numeric
from .normalization import clamp, round6


def quantum_structures(quantum_row: dict[str, Any]) -> dict[str, Any]:
    model_class = str(quantum_row.get("quantum_model_class") or quantum_row.get("quantum_model_class_candidate") or "CLASSICAL_ONLY")
    variable_domain = str(quantum_row.get("variable_domain") or "REAL")
    objective_order = str(quantum_row.get("objective_order") or "QUADRATIC")
    binary = variable_domain in {"BINARY", "MIXED"}
    constrained = model_class in {"CQM", "QUADRATIC_PROGRAM"}
    mapping_structures: list[str] = []
    if model_class == "BQM_QUBO_ISING":
        mapping_structures.extend(["QUBO", "Ising", "BQM"])
    if model_class == "CQM":
        mapping_structures.append("CQM")
    if model_class == "QUADRATIC_PROGRAM":
        mapping_structures.append("QuadraticProgram")
    if variable_domain == "MIXED":
        mapping_structures.extend(["integer variable objective", "continuous variable objective"])
    if binary:
        mapping_structures.append("binary variable objective")
    return {
        "quantum_model_class": model_class,
        "variable_domains": [variable_domain],
        "objective_direction": "MAXIMIZE_EXECUTION_ADJUSTED_NET_EDGE",
        "objective_order": objective_order,
        "objective_terms": [
            "net_edge_after_costs",
            "capacity_score",
            "cost_drag_ratio_penalty",
            "false_discovery_penalty",
        ],
        "constraint_terms": [
            "capacity_limit",
            "condition_scope_match",
            "cluster_redundancy_limit",
        ]
        if constrained
        else ["penalty_encoded_capacity_and_cluster_terms"],
        "penalty_terms": [
            "cost_drag_ratio",
            "latency_drag_ratio",
            "liquidity_drag_ratio",
            "correlation_cluster_penalty",
        ],
        "mapping_structures": mapping_structures or ["classical comparator candidate"],
        "qiskit_candidate": model_class in {"BQM_QUBO_ISING", "CQM", "QUADRATIC_PROGRAM"} or binary,
        "dwave_candidate": model_class in {"BQM_QUBO_ISING", "CQM"} or binary,
        "classical_comparator": quantum_row.get("classical_comparator_ref", "PR166_SM_CLASSICAL_COMPARATOR::NET_EDGE_RANKING"),
    }


def readiness_score(quantum_row: dict[str, Any], refreshed_score: float) -> float:
    model_class = str(quantum_row.get("quantum_model_class") or quantum_row.get("quantum_model_class_candidate") or "CLASSICAL_ONLY")
    variable_domain = str(quantum_row.get("variable_domain") or "REAL")
    base = numeric(quantum_row, "quantum_candidate_selection_score", 0.35)
    structural = 0.25 if model_class != "CLASSICAL_ONLY" else 0.05
    binary_bonus = 0.15 if variable_domain in {"BINARY", "MIXED"} else 0.0
    objective_bonus = 0.10 if str(quantum_row.get("objective_order") or "") == "QUADRATIC" else 0.0
    return round6(clamp(0.45 * base + structural + binary_bonus + objective_bonus + 0.10 * refreshed_score))


def quantum_priority(readiness: float, refreshed_score: float, prior_quantum_score: float) -> tuple[float, float]:
    priority = round6(clamp((0.45 * readiness) + (0.40 * refreshed_score) + (0.15 * prior_quantum_score)))
    return priority, round6(priority - prior_quantum_score)
