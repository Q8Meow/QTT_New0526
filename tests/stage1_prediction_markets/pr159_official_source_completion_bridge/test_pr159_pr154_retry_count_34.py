from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report, pr154_records


def test_pr159_pr154_retry_count_34():
    assert master_report()["pr154_retry_target_count"] == 34
    assert len(pr154_records()) == 34

