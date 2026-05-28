from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_invented_locators():
    assert master_report()["invented_locator_count"] == 0

