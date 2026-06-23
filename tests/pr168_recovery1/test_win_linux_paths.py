from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_win_linux_paths_under_hard_limit() -> None:
    assert_recovery1_valid()
    assert report("PR168_RECOVERY1_FinalSummary.report.json")["records"]["path_audit_failure_count"] == 0
