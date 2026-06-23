from tests.pr168_rank3._helpers import assert_rank3_valid, report


def test_path_audit_has_no_hard_failures() -> None:
    assert_rank3_valid()
    paths = report("PR168_RANK3_PathAudit.report.json")["records"]["rows"]
    assert all(row["path_audit_status"] != "FAIL_HARD_PATH_TOO_LONG" for row in paths)
