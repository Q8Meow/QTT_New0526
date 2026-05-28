from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report, overlay_report


def test_pr158_no_runtime_live_connector_replay_paper_scoring_ranking_selection_optimizer_quantum_profit_authority():
    assert set(master_report()["no_authority_confirmation"].values()) == {False}
    assert overlay_report()["live_order_authority_allowed_count"] == 0
    assert overlay_report()["scoring_execution_allowed_count"] == 0
    assert overlay_report()["optimizer_execution_allowed_count"] == 0
    assert overlay_report()["quantum_backend_execution_allowed_count"] == 0

