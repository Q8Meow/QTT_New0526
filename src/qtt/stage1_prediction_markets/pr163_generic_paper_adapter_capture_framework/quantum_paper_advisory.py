"""Quantum-forward paper advisory records for PR163."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_quantum_rows(
    *,
    index: int,
    row_resolution: dict[str, Any],
    decision_ref: str,
    pretrade_ref: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    quantum_refs = row_resolution.get("quantum_binding_refs", [])
    has_quantum = bool(quantum_refs)
    common = {
        "candidate_packet_id": row_resolution["candidate_packet_id"],
        "qku_ids": row_resolution.get("qku_ids", []),
        "quantum_objective_binding_refs": quantum_refs,
        "quantum_constraint_binding_refs": quantum_refs,
        "quantum_comparator_binding_refs": quantum_refs,
        "paper_decision_intent_ref": decision_ref,
        "paper_pretrade_receipt_ref": pretrade_ref,
        "downstream_pr163_b_paired_replay_paper_executor_ref": plain_ref("PR163B_HANDOFF", index),
        "downstream_pr164_review_provenance_ref": plain_ref("PR164_HANDOFF", index),
        "downstream_pr165_scoring_ranking_ref": plain_ref("PR165_HANDOFF", index),
        "downstream_pr166_llm_review_lane_ref": plain_ref("PR166_HANDOFF", index),
        "hot_path_allowed": False,
        "batch_precompute_only": True,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "quantum_compatibility_status": "QUANTUM_PAPER_ADVISORY_COMPATIBLE" if has_quantum else "NO_QUANTUM_BINDING_FOR_ROW",
        "validation_status": "PASS",
        **no_authority_fields(),
    }
    advisory = {
        "paper_quantum_advisory_input_ref": plain_ref("QUANTUM_ADVISORY_INPUT", index),
        "expected_value_vector_ref": plain_ref("EXPECTED_VALUE_VECTOR", index),
        "probability_vector_ref": plain_ref("PROBABILITY_VECTOR", index),
        "cost_adjusted_price_vector_ref": plain_ref("COST_ADJUSTED_PRICE_VECTOR", index),
        "risk_vector_ref": plain_ref("RISK_VECTOR", index),
        "covariance_matrix_ref": plain_ref("COVARIANCE_MATRIX", index),
        "correlation_matrix_ref": plain_ref("CORRELATION_MATRIX", index),
        "capital_budget_ref": plain_ref("CAPITAL_BUDGET", index),
        "position_limit_ref": plain_ref("POSITION_LIMIT", index),
        "exposure_limit_ref": plain_ref("EXPOSURE_LIMIT", index),
        "liquidity_depth_ref": plain_ref("LIQUIDITY_DEPTH", index),
        "latency_window_ref": plain_ref("LATENCY_WINDOW", index),
        "classical_comparator_ref": row_resolution.get("classical_comparator_binding_refs", []),
        **common,
    }
    constraint = {
        "paper_quantum_constraint_projection_ref": plain_ref("QUANTUM_CONSTRAINT_PROJECTION", index),
        "constraint_projection_status": "BATCH_PRECOMPUTE_INPUT_ONLY",
        **common,
    }
    comparator = {
        "paper_quantum_classical_comparator_trace_ref": plain_ref("QUANTUM_CLASSICAL_COMPARATOR_TRACE", index),
        "classical_comparator_delta_ref_or_value": "PR163_CLASSICAL_COMPARATOR_DELTA_CANDIDATE_ONLY",
        **common,
    }
    hot_path = {
        "paper_quantum_hot_path_exclusion_ref": plain_ref("QUANTUM_HOT_PATH_EXCLUSION", index),
        "quantum_hot_path_allowed": False,
        "quantum_batch_only": True,
        **common,
    }
    return advisory, constraint, comparator, hot_path
