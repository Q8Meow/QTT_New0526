from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_b_registry


def test_pr158_lane_b_conservative_policy_defaults_replay_paper_required():
    for record in lane_b_registry()["records"]:
        assert record["replay_paper_required_before_live"] is True
        assert record["live_blocked_until_owner_review"] is True
        assert record["response_value_or_null"] == "OWNER_APPROVED_CONSERVATIVE_INTERNAL_POLICY_DEFAULT_REPLAY_PAPER_REQUIRED"

