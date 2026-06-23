from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_preflight_pr239_main_ci_guard_passed() -> None:
    assert_recovery1_valid()
    final = report("PR168_RECOVERY1_FinalSummary.report.json")["records"]
    assert final["pr239_merged_preflight_passed_flag"] is True
