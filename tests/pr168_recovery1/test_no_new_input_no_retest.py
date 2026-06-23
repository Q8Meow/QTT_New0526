from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_no_new_input_no_retest_has_changed_hypothesis() -> None:
    assert_recovery1_valid()
    assert all(row["new_TCA_fill_latency_capacity_repair_flag"] for row in rows("no_new_input_no_retest"))
