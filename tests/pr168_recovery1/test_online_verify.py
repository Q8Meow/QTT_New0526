from tests.pr168_recovery1._helpers import assert_recovery1_valid, report, rows


def test_online_verify_materializes_committed_sources() -> None:
    assert_recovery1_valid()
    coverage = report("PR168_RECOVERY1_OnlineVerifyCoverage.report.json")["records"]
    assert coverage["distinct_source_url_count"] >= 16
    assert all(row["source_to_retest_mapping_status"] for row in rows("online_verify"))
