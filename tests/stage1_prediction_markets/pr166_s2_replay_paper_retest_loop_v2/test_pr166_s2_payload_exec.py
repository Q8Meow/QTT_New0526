from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_payload_exec_audit_precedes_episode():
    rows = assert_report_rows("PR166_S2_PayloadExecAudit.report.json", 3215)
    assert all(row["payload_exec_status"] == "REPAIRED_PAYLOAD_SMOKE_EXECUTED_BEFORE_RETEST" for row in rows[:100])
