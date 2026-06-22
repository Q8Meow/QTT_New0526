from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_path_alias_reports_have_no_hard_failures() -> None:
    assert records("PR168_MAP3_FileAliases.report.json")
    rows = records("PR168_MAP3_PathAudit.report.json")
    assert all(row["path_audit_state"] == "PASS" for row in rows)
    assert summary()["path_audit_failure_count"] == 0
