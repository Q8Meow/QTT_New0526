from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_no_orphan_audit_is_clean():
    rows = assert_report_rows("PR166_S2_OrphanArtifactAudit.report.json")
    assert summary()["orphan_rows"] == 0
    assert all(row["orphan_count"] == 0 for row in rows)
