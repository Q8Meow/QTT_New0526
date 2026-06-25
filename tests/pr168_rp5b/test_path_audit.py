from tests.pr168_rp5b._helpers import load_report, load_rows


def test_path_audit() -> None:
    report = load_report("PR168_RP5B_PathAudit.report.json")
    rows = load_rows("path_audit_rows")
    assert rows
    assert report["path_hard_fail_count"] == 0
    assert all(row["physical_path_length"] < 240 for row in rows)
