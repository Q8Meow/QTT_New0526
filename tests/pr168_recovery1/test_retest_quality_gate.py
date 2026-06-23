from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_retest_quality_gate_pass_count_matches_retests() -> None:
    assert_recovery1_valid()
    final = report("PR168_RECOVERY1_FinalSummary.report.json")["records"]
    assert final["retest_quality_gate_pass_count"] == final["retest_before_after_count"]
    assert final["retest_quality_gate_fail_count"] == 0
