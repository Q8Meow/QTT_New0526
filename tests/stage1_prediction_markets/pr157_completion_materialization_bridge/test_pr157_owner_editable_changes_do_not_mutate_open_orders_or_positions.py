from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_owner_editable_changes_do_not_mutate_open_orders_or_positions():
    for record in atomic_records():
        assert record["open_orders_unchanged_by_value_change_flag"] is True
        assert record["open_positions_unchanged_by_value_change_flag"] is True
