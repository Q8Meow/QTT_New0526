from __future__ import annotations


def test_authority_boundary_counts_are_zero(pr165_d2_records, pr165_d2_summary):
    row = pr165_d2_records["PR165_D2_AuthorityBoundaryAudit.report.json"][0]
    for field in (
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
    ):
        assert row[field] == 0
        assert pr165_d2_summary[field] == 0
