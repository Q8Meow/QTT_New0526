from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_path_alias_has_no_hard_failures() -> None:
    assert_recovery1_valid()
    rows = report("PR168_RECOVERY1_PathAudit.report.json")["records"]["rows"]
    assert rows
    assert all(row["path_audit_state"] != "HARD_FAIL" for row in rows)
