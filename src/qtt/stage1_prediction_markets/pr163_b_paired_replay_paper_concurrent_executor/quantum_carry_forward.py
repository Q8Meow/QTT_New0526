"""Quantum-forward advisory carry-through without backend execution."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_quantum_carry(index: int, ctx: dict[str, Any], divergence: dict[str, Any], tca: dict[str, Any]) -> dict[str, Any]:
    row = ctx["row"]
    paper_quantum = ctx["paper"]["quantum"]
    return {
        "quantum_carry_ref": plain_ref("QUANTUM_CARRY", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": list(row.get("qku_ids") or []),
        "quantum_objective_binding_refs": list(row.get("quantum_binding_refs") or []),
        "quantum_constraint_binding_refs": list(row.get("quantum_binding_refs") or []),
        "quantum_comparator_binding_refs": list(row.get("quantum_binding_refs") or []),
        "expected_value_vector_ref": paper_quantum.get("expected_value_vector_ref", plain_ref("EXPECTED_VALUE_VECTOR", index)),
        "probability_vector_ref": paper_quantum.get("probability_vector_ref", plain_ref("PROBABILITY_VECTOR", index)),
        "cost_adjusted_price_vector_replay_ref": plain_ref("REPLAY_COST_PRICE_VECTOR", index),
        "cost_adjusted_price_vector_paper_ref": paper_quantum.get("cost_adjusted_price_vector_ref", plain_ref("PAPER_COST_PRICE_VECTOR", index)),
        "risk_vector_ref": plain_ref("RISK_VECTOR", index),
        "covariance_matrix_ref": paper_quantum.get("covariance_matrix_ref", plain_ref("COVARIANCE_MATRIX", index)),
        "correlation_matrix_ref": paper_quantum.get("correlation_matrix_ref", plain_ref("CORRELATION_MATRIX", index)),
        "liquidity_depth_ref": paper_quantum.get("liquidity_depth_ref", plain_ref("LIQUIDITY_DEPTH", index)),
        "latency_window_ref": paper_quantum.get("latency_window_ref", plain_ref("LATENCY_WINDOW", index)),
        "capital_budget_ref": paper_quantum.get("capital_budget_ref", plain_ref("CAPITAL_BUDGET", index)),
        "exposure_limit_ref": paper_quantum.get("exposure_limit_ref", plain_ref("EXPOSURE_LIMIT", index)),
        "constraint_pressure_candidate": "QUANTUM_BOUND_CONSTRAINT_PRESSURE_CANDIDATE" if row.get("quantum_binding_refs") else "CLASSICAL_ONLY_EXACT_REASON",
        "replay_paper_divergence_refs": [divergence["divergence_ref"]],
        "tca_refs": [tca["tca_ref"]],
        "classical_comparator_refs": list(row.get("classical_comparator_binding_refs") or paper_quantum.get("classical_comparator_ref") or []),
        "hot_path_allowed": False,
        "batch_precompute_only": True,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "downstream_pr165_ref": plain_ref("PR165_HANDOFF", index),
        "validation_status": "PASS",
        **no_authority_fields(),
    }
