from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_status_drift_audit_is_clean():
    rows = assert_report_contract("PR166_SM3_StatusDriftAudit.report.json", 1)
    assert rows[0]["status_drift_count"] == 0
