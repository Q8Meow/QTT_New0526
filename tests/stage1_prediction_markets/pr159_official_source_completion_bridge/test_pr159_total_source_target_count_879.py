from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report, target_records


def test_pr159_total_source_target_count_879():
    assert master_report()["retrieval_target_count"] == 879
    assert len(target_records()) == 879

