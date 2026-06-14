from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_sm2_no_orphan_audit_covers_reports():
    rows = assert_report_rows("PR166_SM2_OrphanAudit.report.json", 102)
    assert all(row["orphan_rows"] == 0 for row in rows)
    assert summary()["orphan_rows"] == 0
