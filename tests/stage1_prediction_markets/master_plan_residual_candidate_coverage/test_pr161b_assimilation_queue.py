from .pr161b_test_support import candidate_records, records, summary


def test_pr161b_assimilation_queue_covers_all_required_residuals():
    queue_ids = {record["residual_candidate_id"] for record in records("assimilation_queue")}
    required = {record["residual_candidate_id"] for record in candidate_records() if record["pr161c_assimilation_required_flag"]}
    assert queue_ids == required
    assert summary()["pr161c_assimilation_queue_count"] == len(queue_ids)
