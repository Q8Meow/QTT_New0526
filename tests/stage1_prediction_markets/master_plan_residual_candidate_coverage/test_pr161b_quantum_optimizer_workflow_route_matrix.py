from .pr161b_test_support import records, summary


def test_pr161b_quantum_optimizer_workflow_routes_do_not_execute_backends():
    assert summary()["quantum_optimizer_workflow_route_count"] == len(records("quantum_optimizer_workflow"))
    assert all(record["quantum_backend_execution_evidence_created_flag"] is False for record in records("quantum_optimizer_workflow")[:25])
