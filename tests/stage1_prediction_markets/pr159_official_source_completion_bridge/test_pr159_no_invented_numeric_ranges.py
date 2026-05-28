from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_invented_numeric_ranges():
    assert master_report()["invented_numeric_range_count"] == 0

