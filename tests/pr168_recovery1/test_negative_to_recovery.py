from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_negative_to_recovery_has_causal_chain() -> None:
    assert_recovery1_valid()
    assert all(row["failure_cause_code"] and row["repair_action_ref"] and row["after_retest_row_ref"] for row in rows("negative_to_recovery"))
