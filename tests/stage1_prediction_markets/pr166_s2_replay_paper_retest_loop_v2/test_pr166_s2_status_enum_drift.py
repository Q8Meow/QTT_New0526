from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_status_enum_drift_audit_is_clean():
    row = assert_report_rows("PR166_S2_StatusEnumDriftAudit.report.json", 1)[0]
    assert row["forbidden_token_occurrence_count"] == 0
    assert summary()["unknown_status_rows"] == 0
