from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_no_lookahead_flags_false() -> None:
    assert_recovery1_valid()
    assert all(not row["outcome_used_for_decision_flag"] and not row["lookahead_leakage_flag"] for row in rows("retest_before_after"))
