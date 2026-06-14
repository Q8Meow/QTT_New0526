from __future__ import annotations

from .helpers import report_rows


def test_pr166_sf_r2_no_profit_evidence_audit():
    rows = report_rows("PR166_SF_R2_NoProfitAudit.report.json")
    assert rows[0]["no_profit_audit_status"] == "PASS"
    assert rows[0]["profit_evidence_count"] == 0
    assert rows[0]["positive_rows_are_replay_paper_only"] is True
