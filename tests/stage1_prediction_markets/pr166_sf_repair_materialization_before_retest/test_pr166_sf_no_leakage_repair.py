from .conftest import assert_rows


def test_pr166_sf_no_leakage_audit_preserves_boundaries(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_NoLeakageRepairAudit.report.json")
    assert all(row["point_in_time_no_leakage_status"].startswith("POINT_IN_TIME") for row in rows[:100])
    assert all(row["stale_feature_risk"] == "RETEST_REQUIRED_BEFORE_PROMOTION" for row in rows[:100])
