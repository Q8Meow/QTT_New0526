from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_side_effect_cleanup_forbidden_prefix_count_zero() -> None:
    assert_recovery1_valid()
    assert report("PR168_RECOVERY1_SideEffectCleanupAudit.report.json")["records"]["forbidden_prefix_changed_count"] == 0
