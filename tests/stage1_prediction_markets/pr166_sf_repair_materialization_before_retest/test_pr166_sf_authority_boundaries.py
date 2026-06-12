from .conftest import assert_rows


def test_pr166_sf_authority_counts_are_zero(pr166_sf_records, pr166_sf_summary):
    rows = assert_rows(pr166_sf_records, "PR166_SF_AuthorityBoundaryAudit.report.json")
    for field in ("source_truth_acceptance_count", "connector_semantic_binding_count", "private_state_fetch_count", "runtime_cash_receipt_count", "live_order_authority_count", "profit_evidence_count", "quantum_backend_execution_count", "quantum_advantage_claim_count", "new_sha256_artifact_count"):
        assert rows[0][field] == 0
        assert pr166_sf_summary[field] == 0
