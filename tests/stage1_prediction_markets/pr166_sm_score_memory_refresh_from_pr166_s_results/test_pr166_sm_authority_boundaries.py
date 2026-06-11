AUTHORITY_ZERO_FIELDS = [
    "source_truth_acceptance_count",
    "connector_semantic_binding_count",
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
]


def test_pr166_sm_authority_boundary_audit_is_zero(pr166_sm_records):
    row = pr166_sm_records["PR166_SM_AuthorityBoundaryAudit.report.json"][0]
    assert row["audit_result"] == "PASS"
    for field in AUTHORITY_ZERO_FIELDS:
        assert row[field] == 0


def test_pr166_sm_summary_reports_no_forbidden_authority(pr166_sm_summary):
    for field in [
        "authority_violation_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "live_order_authority_count",
        "profit_evidence_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_authority_count",
        "atomicrows_bundle_sha_reference_count",
        "new_sha256_artifact_count",
    ]:
        assert pr166_sm_summary[field] == 0
