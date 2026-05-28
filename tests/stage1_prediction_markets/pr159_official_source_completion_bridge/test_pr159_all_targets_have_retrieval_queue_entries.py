from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import target_records


def test_pr159_all_targets_have_retrieval_queue_entries():
    assert all(record["official_source_target_ids"] for record in target_records())

