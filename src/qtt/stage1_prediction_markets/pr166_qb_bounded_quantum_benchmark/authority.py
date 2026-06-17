"""Central authority defaults for PR166-QB."""

from __future__ import annotations

ZERO_AUTHORITY_KEYS: tuple[str, ...] = (
    "live_order_authority_count",
    "live_promotion_claim_count",
    "owner_live_approval_receipt_count",
    "source_truth_acceptance_count",
    "connector_semantic_binding_count",
    "connector_truth_count",
    "venue_account_truth_count",
    "private_state_fetch_count",
    "runtime_cash_receipt_count",
    "profit_evidence_count",
    "cloud_backend_execution_count",
    "credential_access_count",
    "quantum_backend_execution_count",
    "quantum_advantage_claim_count",
    "provider_api_call_count",
    "llm_hot_path_order_release_count",
    "llm_hot_path_artifact_count",
    "llm_order_release_artifact_count",
    "llm_source_acceptance_artifact_count",
    "llm_result_rewrite_artifact_count",
    "qtt_sha_authority_count",
    "qtt_sha_freeze_checksum_global_digest_authority_count",
    "atomicrows_bundle_hash_authority_count",
    "atomicrows_bundle_sha_hash_checksum_authority_count",
    "metadata_only_count",
    "solver_label_only_count",
    "placeholder_count",
    "future_consumer_note_only_count",
    "unknown_status_count",
    "orphan_count",
)

FORBIDDEN_AUTHORITY_FLAGS: tuple[str, ...] = (
    "cloud_backend_execution_flag",
    "credential_access_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "live_order_authority_flag",
    "profit_evidence_flag",
    "source_truth_acceptance_flag",
    "connector_semantic_binding_flag",
    "private_state_fetch_flag",
    "runtime_cash_receipt_flag",
)


def authority_zero_counts() -> dict[str, int]:
    return {key: 0 for key in ZERO_AUTHORITY_KEYS}


def authority_false_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_AUTHORITY_FLAGS}


def authority_boundary_record() -> dict[str, object]:
    return {
        "authority_scope": "PR166_QB_BOUNDED_NONLIVE_QUANTUM_BENCHMARK_ONLY",
        "cloud_quantum_backend_execution_allowed_in_this_pr": False,
        "credential_access_allowed_in_this_pr": False,
        "provider_api_calls_allowed_in_this_pr": False,
        "quantum_backend_execution_allowed_in_this_pr": False,
        "quantum_advantage_claim_allowed_in_this_pr": False,
        "live_order_authority_allowed_in_this_pr": False,
        "live_promotion_claim_allowed_in_this_pr": False,
        "owner_live_approval_receipt_allowed_in_this_pr": False,
        "source_truth_acceptance_allowed_in_this_pr": False,
        "connector_semantic_binding_allowed_in_this_pr": False,
        "private_state_fetch_allowed_in_this_pr": False,
        "runtime_cash_receipt_allowed_in_this_pr": False,
        "profit_evidence_allowed_in_this_pr": False,
        "qtt_sha_authority_allowed_in_this_pr": False,
        "atomicrows_bundle_hash_authority_allowed_in_this_pr": False,
        "candidate_values_route": "REPLAY_PAPER_OR_OWNER_AGENT_REVIEW_BEFORE_ANY_PROMOTION",
    }
