from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_report


def test_pr157_atomicrows_no_placeholder_values():
    assert atomic_report()["placeholder_value_count"] == 0
