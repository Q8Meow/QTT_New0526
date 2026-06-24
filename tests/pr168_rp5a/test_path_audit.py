from tests.pr168_rp5a._helpers import load_report


def test_path_audit() -> None:
    report = load_report("PR168_RP5A_PathAudit.report.json")
    assert report["path_hard_fail_count"] == 0
    assert all(row["physical_path_length"] < row["hard_fail_physical_path_length"] for row in report["records"])
