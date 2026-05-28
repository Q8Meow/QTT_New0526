from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_optimizer_execution():
    assert master_report()["optimizer_execution_count"] == 0
    assert master_report()["no_authority_confirmation"]["optimizer_execution_created"] is False

