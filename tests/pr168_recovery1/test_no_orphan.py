from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_no_orphan_count_zero() -> None:
    assert_recovery1_valid()
    assert report("PR168_RECOVERY1_FinalSummary.report.json")["records"]["no_orphan_violation_count"] == 0
