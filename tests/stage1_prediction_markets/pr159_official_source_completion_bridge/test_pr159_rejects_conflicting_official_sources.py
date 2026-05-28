from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import accepted_records, master_report


def test_pr159_rejects_conflicting_official_sources():
    assert master_report()["conflict_blocked_count"] == 0
    assert all(record["conflict_cleared_flag"] is True for record in accepted_records())

