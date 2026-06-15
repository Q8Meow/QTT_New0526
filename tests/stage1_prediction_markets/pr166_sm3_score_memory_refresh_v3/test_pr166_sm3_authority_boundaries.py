from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_sm3_forbidden_authority_counts_remain_zero():
    assert_report_contract("PR166_SM3_AuthorityAudit.report.json", 1)
    s = summary()
    for field in (
        "live_order_authority_count",
        "live_promotion_claim_count",
        "owner_live_approval_receipt_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "profit_evidence_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "llm_hot_path_order_release_count",
        "qtt_sha_authority_count",
        "atomicrows_bundle_hash_authority_count",
    ):
        assert s[field] == 0, field
