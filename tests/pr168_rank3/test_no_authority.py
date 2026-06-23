from tests.pr168_rank3._helpers import assert_rank3_valid, report


def test_rank3_forbidden_authority_counts_zero() -> None:
    assert_rank3_valid()
    final = report("PR168_RANK3_FinalSummary.report.json")["records"]
    for field in ("real_positive_count", "real_negative_count", "champion_allowed_count", "live_candidate_allowed_count", "source_truth_acceptance_created_count", "order_authority_created_count", "quantum_backend_execution_count", "quantum_advantage_claim_count", "qtt_sha_or_atomicrows_hash_authority_count"):
        assert final[field] == 0
