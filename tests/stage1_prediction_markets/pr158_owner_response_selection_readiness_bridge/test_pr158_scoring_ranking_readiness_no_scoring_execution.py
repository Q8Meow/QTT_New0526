from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import overlay_report, overlay_records


def test_pr158_scoring_ranking_readiness_no_scoring_execution():
    assert overlay_report()["scoring_execution_allowed_count"] == 0
    assert all(record["scoring_execution_allowed_flag"] is False for record in overlay_records())

