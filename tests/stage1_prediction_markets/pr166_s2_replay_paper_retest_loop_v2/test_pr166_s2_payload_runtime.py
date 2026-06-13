from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_payload_runtime_audit_verifies_schema_and_vectors():
    rows = assert_report_rows("PR166_S2_PayloadRuntimeAudit.report.json", 3215)
    assert all(row["input_schema_verified_flag"] is True for row in rows[:100])
    assert all(row["test_vector_compatibility_verified_flag"] is True for row in rows[:100])
