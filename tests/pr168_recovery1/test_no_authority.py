from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_no_forbidden_authority_counts_zero() -> None:
    assert_recovery1_valid()
    final = report("PR168_RECOVERY1_FinalSummary.report.json")["records"]
    for field in ("real_positive_count", "real_negative_count", "champion_allowed_count", "live_candidate_allowed_count", "source_truth_acceptance_created_count", "connector_binding_created_count", "private_state_or_cash_access_created_count", "order_authority_created_count", "quantum_backend_execution_count", "quantum_advantage_claim_count", "qtt_sha_or_atomicrows_hash_authority_count"):
        assert final[field] == 0
