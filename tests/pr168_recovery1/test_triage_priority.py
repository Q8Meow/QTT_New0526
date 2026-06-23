from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_triage_priority_has_apply_or_defer_decision() -> None:
    assert_recovery1_valid()
    assert all(row["apply_repair_now_flag"] or row["defer_with_reason_flag"] for row in rows("triage_priority"))
