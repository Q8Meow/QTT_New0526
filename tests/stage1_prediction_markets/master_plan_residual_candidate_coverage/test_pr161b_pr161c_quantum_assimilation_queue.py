from .pr161b_test_support import records, summary


def test_pr161b_uncovered_quantum_residuals_create_pr161c_queue_records():
    assert summary()["quantum_pr161c_assimilation_queue_count"] == len(records("quantum_assimilation_queue"))
    for record in records("quantum_assimilation_queue"):
        assert record["quantum_backend_execution_allowed_flag"] is False
        assert record["optimizer_execution_allowed_flag"] is False
