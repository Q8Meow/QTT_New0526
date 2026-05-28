from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_invented_external_facts():
    assert master_report()["invented_external_fact_count"] == 0

