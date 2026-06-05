"""Quantum-forward binding packet builders."""

from __future__ import annotations

from typing import Any


QUANTUM_FAMILIES = (
    "QUANTUM_OBJECTIVE_INPUTS",
    "QUANTUM_VARIABLE_DOMAIN_INPUTS",
    "QUANTUM_CONSTRAINT_INPUTS",
)
SUPPORTED_MODEL_FAMILIES = (
    "QUBO",
    "BQM",
    "ISING",
    "CQM",
    "QAOA_COMPATIBLE",
    "VQE_COMPATIBLE",
    "ANNEALING_COMPATIBLE",
    "HYBRID_CLASSICAL_QUANTUM",
    "CLASSICAL_COMPARATOR_ONLY",
)


def _quantum_packet(binding: dict[str, Any], prefix: str, status: str) -> dict[str, Any]:
    return {
        **binding,
        "binding_id": f"{prefix}::{binding['binding_id'].split('::')[-1]}",
        "dataset_binding_ref": binding["binding_id"],
        "quantum_binding_status": status,
        "supported_model_families": list(SUPPORTED_MODEL_FAMILIES),
        "expected_value_vector": [0.03, 0.04, 0.02],
        "probability_vector": [0.54, 0.61, 0.48],
        "cost_adjusted_price_vector": [0.49, 0.55, 0.44],
        "risk_vector": [0.12, 0.16, 0.10],
        "covariance_matrix_ref": "synthetic_quantum_objective_inputs.fixture.json::covariance_matrix",
        "correlation_matrix_ref": "synthetic_quantum_objective_inputs.fixture.json::correlation_matrix",
        "capital_budget": 1000.0,
        "position_size_limit": 100.0,
        "drawdown_limit": 0.08,
        "exposure_limit": 0.25,
        "venue_eligibility_vector": [1, 1, 0],
        "liquidity_depth_vector": [500, 420, 380],
        "latency_window": "QUANTUM_BATCH_ONLY",
        "settlement_risk_vector": [0.02, 0.03, 0.01],
        "objective_scale": 1.0,
        "variable_domain_map": {"x0": "BINARY", "x1": "BINARY", "x2": "BINARY"},
        "constraint_matrix_or_terms": [[1, 1, 1], [0.49, 0.55, 0.44]],
        "penalty_weights": {"budget": 3.0, "exposure": 2.0, "liquidity": 1.0},
        "classical_comparator_ref": "PR162R_B_CLASSICAL_COMPARATOR_INPUT_BINDING",
        "comparator_input_binding_ref": "synthetic_classical_comparator_inputs.fixture.json",
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "validation_status": "PASS",
    }


def build_quantum_objective_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _quantum_packet(binding, "PR162R_B_QUANTUM_OBJECTIVE_INPUT_BINDING", "QUANTUM_OBJECTIVE_INPUT_BOUND")
        for binding in dataset_bindings
        if binding["binding_family"] == "QUANTUM_OBJECTIVE_INPUTS"
    ]


def build_quantum_constraint_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _quantum_packet(binding, "PR162R_B_QUANTUM_CONSTRAINT_INPUT_BINDING", "QUANTUM_CONSTRAINT_INPUT_BOUND")
        for binding in dataset_bindings
        if binding["binding_family"] in {"QUANTUM_CONSTRAINT_INPUTS", "QUANTUM_VARIABLE_DOMAIN_INPUTS"}
    ]


def build_quantum_comparator_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _quantum_packet(binding, "PR162R_B_QUANTUM_COMPARATOR_DATASET_BINDING", "QUANTUM_COMPARATOR_INPUT_BOUND")
        for binding in dataset_bindings
        if binding["binding_family"] in QUANTUM_FAMILIES
    ]


def quantum_binding_lookup(dataset_bindings: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for binding in dataset_bindings:
        if binding["binding_family"] not in QUANTUM_FAMILIES:
            continue
        for packet_id in binding.get("consumer_candidate_packet_ids", []):
            lookup.setdefault(packet_id, []).append(binding["binding_id"])
    return {key: sorted(value) for key, value in lookup.items()}
