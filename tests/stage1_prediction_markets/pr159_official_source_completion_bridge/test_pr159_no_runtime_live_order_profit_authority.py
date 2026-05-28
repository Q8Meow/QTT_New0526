from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_runtime_live_order_profit_authority():
    assert master_report()["runtime_live_order_profit_authority_count"] == 0
    assert master_report()["no_authority_confirmation"]["order_authority_created"] is False
    assert master_report()["no_authority_confirmation"]["profit_evidence_created"] is False

