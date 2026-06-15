from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_status_drift_forbidden_token_count_is_zero():
    rows = assert_report_contract("PR166_SM3_StatusDriftAudit.report.json", 1)
    assert rows[0]["forbidden_status_token_count"] == 0
