from .conftest import assert_rows


def test_pr166_sf_no_orphan_audit_passes(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_OrphanArtifactAudit.report.json")
    assert rows[0]["orphan_rows"] == 0
    assert rows[0]["orphan_artifacts"] == 0
    assert rows[0]["no_orphan_audit_result"] == "PASS"
