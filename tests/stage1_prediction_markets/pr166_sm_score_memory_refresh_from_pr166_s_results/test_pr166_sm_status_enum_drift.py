def test_pr166_sm_status_enum_drift_audit_is_clean(pr166_sm_records):
    row = pr166_sm_records["PR166_SM_StatusEnumDriftAudit.report.json"][0]
    assert row["audit_result"] == "PASS"
    assert row["unauthorized_status_enum_drift_count"] == 0


def test_pr166_sm_manifest_uses_central_schema_refs(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_ReportManifest.report.json"]
    assert len(rows) == 38
    for row in rows:
        assert row["schema_ref"]
        assert row["schema_path"].endswith(row["schema_ref"])
        assert row["no_orphan_status"] == "CONNECTED_UPSTREAM_AND_DOWNSTREAM"
