from tests.pr168_rp5b._helpers import final_summary


def test_no_live_order_or_source_truth_authority() -> None:
    summary = final_summary()
    assert summary["live_order_authority_created_count"] == 0
    assert summary["source_truth_authority_created_count"] == 0
    assert summary["quantum_backend_execution_count"] == 0
    assert summary["qtt_sha_or_atomicrows_hash_authority_count"] == 0
