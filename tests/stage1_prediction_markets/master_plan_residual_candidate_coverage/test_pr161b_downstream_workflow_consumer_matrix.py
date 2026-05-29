from .pr161b_test_support import records, summary


def test_pr161b_downstream_workflow_consumer_matrix_is_complete():
    assert summary()["downstream_workflow_consumer_record_count"] == len(records("downstream_workflow"))
    assert all(record["workflow_consumption_state"] for record in records("downstream_workflow")[:25])
