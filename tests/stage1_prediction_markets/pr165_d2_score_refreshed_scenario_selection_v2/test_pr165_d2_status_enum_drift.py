from __future__ import annotations


def test_status_enum_drift_audit_passes(pr165_d2_records, pr165_d2_summary):
    row = pr165_d2_records["PR165_D2_StatusEnumDriftAudit.report.json"][0]
    assert row["unauthorized_status_enum_drift_count"] == 0
    assert row["status_enum_drift_audit_result"] == "PASS"
    assert pr165_d2_summary["unknown_status_rows"] == 0
