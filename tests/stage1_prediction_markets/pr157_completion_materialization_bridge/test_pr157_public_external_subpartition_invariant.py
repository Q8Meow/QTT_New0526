from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_report


def test_pr157_public_external_subpartition_invariant():
    receipt = pr154_report()["count_invariant_receipt"]
    assert receipt["public_external_subpartition_counts"] == {
        "captured_candidates": 92,
        "pr153r_retry_candidates": 34,
    }
    assert receipt["public_external_subpartition_sum"] == 126
