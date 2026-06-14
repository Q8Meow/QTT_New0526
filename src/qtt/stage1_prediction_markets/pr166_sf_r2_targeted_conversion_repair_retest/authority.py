"""Authority boundary helpers for PR166-SF-R2."""

from __future__ import annotations

ZERO_AUTHORITY_KEYS: tuple[str, ...] = (
    "live_order_authority_count",
    "live_promotion_claim_count",
    "source_truth_acceptance_count",
    "connector_semantic_binding_count",
    "connector_truth_count",
    "venue_account_truth_count",
    "private_state_fetch_count",
    "runtime_cash_receipt_count",
    "profit_evidence_count",
    "quantum_backend_execution_count",
    "quantum_advantage_claim_count",
    "llm_hot_path_artifact_count",
    "llm_order_release_artifact_count",
    "llm_source_acceptance_artifact_count",
    "llm_result_rewrite_artifact_count",
    "qtt_sha_freeze_checksum_global_digest_authority_count",
    "atomicrows_bundle_sha_hash_checksum_authority_count",
    "metadata_only_count",
    "placeholder_count",
    "unknown_status_count",
    "orphan_count",
)


def authority_zero_counts() -> dict[str, int]:
    return {key: 0 for key in ZERO_AUTHORITY_KEYS}


def authority_boundary_record() -> dict[str, object]:
    return {
        "authority_scope": "REPLAY_PAPER_REPAIR_RETEST_ONLY",
        "positive_label_allowed": (
            "REPAIRED_REPLAY_PAPER_POSITIVE_EDGE_NOT_PROFIT_EVIDENCE"
        ),
        "live_order_authority_allowed_in_this_pr": False,
        "live_promotion_claim_allowed_in_this_pr": False,
        "source_truth_acceptance_allowed_in_this_pr": False,
        "connector_binding_allowed_in_this_pr": False,
        "private_state_fetch_allowed_in_this_pr": False,
        "runtime_cash_receipt_allowed_in_this_pr": False,
        "profit_evidence_allowed_in_this_pr": False,
        "quantum_backend_execution_allowed_in_this_pr": False,
        "quantum_advantage_claim_allowed_in_this_pr": False,
        "qtt_sha_authority_allowed_in_this_pr": False,
        "atomicrows_bundle_hash_authority_allowed_in_this_pr": False,
    }
