from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_owner_editable_changes_route_to_replay_paper_and_block_live():
    editable = [record for record in atomic_records() if record["owner_value_change_allowed_flag"] is True]
    assert editable
    assert all(record["owner_change_requires_replay_flag"] for record in editable)
    assert all(record["owner_change_requires_paper_flag"] for record in editable)
    assert all(record["owner_change_blocks_live_until_review_flag"] for record in editable)
