from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_q_classical_compare_has_fallback_no_advantage_claim() -> None:
    assert_recovery1_valid()
    assert all(row["comparable_classical_fallback_ref"] and not row["quantum_advantage_claim_flag"] for row in rows("q_classical_compare"))
