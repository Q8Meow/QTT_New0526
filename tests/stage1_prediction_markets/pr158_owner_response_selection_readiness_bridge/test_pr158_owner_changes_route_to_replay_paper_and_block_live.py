from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_registry


def test_pr158_owner_changes_route_to_replay_paper_and_block_live():
    for record in master_registry()["records"]:
        if record.get("owner_value_change_allowed_flag") is True:
            assert record["owner_change_requires_replay_flag"] is True
            assert record["owner_change_requires_paper_flag"] is True
            assert record["owner_change_blocks_live_until_review_flag"] is True

