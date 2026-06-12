from .conftest import assert_rows


def test_pr166_sf_materialization_audit_rejects_metadata_only_rows(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_MaterializationAudit.report.json")
    assert len(rows) == 6502
    assert all(row["metadata_only_row_flag"] is False for row in rows[:100])
    assert all(row["candidate_fill_or_route_present_flag"] is True for row in rows[:100])
