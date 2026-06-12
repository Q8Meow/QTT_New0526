"""Central authority-boundary helpers for PR166-SF."""

from __future__ import annotations

from . import constants as c


ZERO_AUTHORITY_KEYS: tuple[str, ...] = (
    "source_truth_acceptance_count",
    "connector_semantic_binding_count",
    "connector_truth_count",
    "venue_account_truth_count",
    "private_state_fetch_count",
    "runtime_cash_receipt_count",
    "live_order_authority_count",
    "live_promotion_claim_count",
    "profit_evidence_count",
    "quantum_backend_execution_count",
    "quantum_advantage_claim_count",
    "llm_hot_path_artifact_count",
    "llm_order_release_artifact_count",
    "llm_source_acceptance_artifact_count",
    "llm_result_rewrite_artifact_count",
    "qtt_sha_freeze_checksum_global_digest_authority_count",
    "atomicrows_bundle_sha_hash_checksum_authority_count",
    "new_sha256_artifact_count",
)


def authority_zero_counts() -> dict[str, int]:
    return {key: 0 for key in ZERO_AUTHORITY_KEYS}


def authority_boundary_record() -> dict[str, object]:
    return {
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "created_by_pr": c.PR_ID,
        "repair_materialization_replay_paper_only": True,
        "source_truth_acceptance_allowed": False,
        "connector_semantic_binding_allowed": False,
        "connector_truth_allowed": False,
        "venue_account_truth_allowed": False,
        "private_state_fetch_allowed": False,
        "runtime_cash_receipt_allowed": False,
        "live_order_authority_allowed": False,
        "live_promotion_claim_allowed": False,
        "profit_evidence_allowed": False,
        "quantum_backend_execution_allowed": False,
        "quantum_advantage_claim_allowed": False,
        "llm_hot_path_authority_allowed": False,
        "qtt_sha_freeze_checksum_global_digest_authority_allowed": False,
        "atomicrows_bundle_sha_hash_checksum_authority_allowed": False,
        **authority_zero_counts(),
    }
