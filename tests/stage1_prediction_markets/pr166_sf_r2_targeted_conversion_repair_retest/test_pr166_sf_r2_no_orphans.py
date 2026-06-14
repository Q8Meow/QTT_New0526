from __future__ import annotations

from .helpers import report_rows


def test_pr166_sf_r2_no_orphan_audit_covers_repair_universe():
    rows = report_rows("PR166_SF_R2_OrphanAudit.report.json")
    assert rows[0]["orphan_audit_status"] == "PASS"
    assert rows[0]["orphan_count"] == 0
    assert rows[0]["covered_candidate_rows"] == 3213
