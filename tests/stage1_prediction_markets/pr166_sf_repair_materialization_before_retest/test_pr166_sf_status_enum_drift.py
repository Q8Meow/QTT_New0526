from .conftest import assert_rows


def test_pr166_sf_status_enum_drift_audit_passes(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_StatusEnumDriftAudit.report.json")
    assert rows[0]["forbidden_status_value_hits"] == 0
    assert rows[0]["status_enum_drift_audit_result"] == "PASS"
