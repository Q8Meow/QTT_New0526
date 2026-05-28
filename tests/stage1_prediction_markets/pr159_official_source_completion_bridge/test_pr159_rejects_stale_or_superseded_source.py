from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import accepted_records, master_report


def test_pr159_rejects_stale_or_superseded_source():
    assert master_report()["stale_revalidation_blocked_count"] == 0
    assert all(record["freshness_valid_flag"] is True for record in accepted_records())

