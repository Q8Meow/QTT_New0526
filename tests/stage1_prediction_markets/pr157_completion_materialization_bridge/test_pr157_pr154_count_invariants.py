from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_report


def test_pr157_pr154_count_invariants():
    receipt = pr154_report()["count_invariant_receipt"]
    assert receipt["total_pr154_targets"] == 342
    assert receipt["base_partition_sum"] == 342
    assert receipt["count_invariants_passed_flag"] is True
