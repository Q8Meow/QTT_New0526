from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_registry


def test_pr157_unresolved_items_have_exact_next_action():
    unresolved = [record for record in pr154_registry()["records"] if record["remaining_blockers"]]
    assert unresolved
    assert all(record["exact_next_action_if_not_complete"] for record in unresolved)
