from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_report


def test_pr157_orphan_count_zero():
    assert atomic_report()["orphan_count"] == 0
