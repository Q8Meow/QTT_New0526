from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_offline_ci_uses_committed_artifacts() -> None:
    assert_recovery1_valid()
    plan = report("PR168_RECOVERY1_DeepOnlineSearchPlan.report.json")["records"]
    assert plan["triggered_flag"] is False
