from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_sm2_status_enum_drift_audit_passes():
    row = assert_report_rows("PR166_SM2_StatusDriftAudit.report.json", 1)[0]
    assert row["unauthorized_token_occurrence_count"] == 0
    assert summary()["unknown_status_rows"] == 0
