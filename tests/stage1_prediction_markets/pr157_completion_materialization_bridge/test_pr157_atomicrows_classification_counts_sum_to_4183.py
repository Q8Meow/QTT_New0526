from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_report


def test_pr157_atomicrows_classification_counts_sum_to_4183():
    counts = atomic_report()["source_requirement_class_counts"]
    total = sum(
        value
        for key, value in counts.items()
        if key.endswith("_count") and key != "atomicrows_total_count"
    )
    assert total == 4183
