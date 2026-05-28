from .helpers import counts


def test_pr159r_pr160_requeue_count_3_reconciled_no_double_count(pr159r_artifacts):
    receipt = counts(pr159r_artifacts)
    assert receipt["pr160_pr159r_requeue_count"] == 3
    assert all(record["incremented_PR159R_869_target_universe_flag"] is False for record in pr159r_artifacts["requeue"]["records"])

