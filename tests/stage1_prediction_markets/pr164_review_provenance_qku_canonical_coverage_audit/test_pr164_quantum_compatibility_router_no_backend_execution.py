from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_quantum_compatibility_router_no_backend_execution():
    rows = load_records("PR164_QuantumCompatibilityRouter.report.json")
    assert summary()["quantum_eligible_rows"] > 0
    assert all(row["quantum_backend_execution_allowed_flag"] is False for row in rows)
    assert all(row["quantum_advantage_claim_allowed_flag"] is False for row in rows)
