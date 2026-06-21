from tests.pr168_gfp2r._helpers import final_summary, rows


def test_pr168_gfp2r_quantum_no_backend_no_advantage() -> None:
    assert final_summary()["quantum_backend_execution_count"] == 0
    assert final_summary()["quantum_advantage_claim_count"] == 0
    assert all(row["quantum_backend_execution_flag"] is False for row in rows("quantum_candidate_stack"))
    assert all(row["quantum_advantage_claim_flag"] is False for row in rows("quantum_candidate_stack"))
