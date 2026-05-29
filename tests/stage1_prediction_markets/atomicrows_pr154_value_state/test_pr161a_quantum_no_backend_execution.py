from .pr161a_test_support import records, summary


def test_pr161a_quantum_no_backend_optimizer_or_advantage_evidence():
    profiles = records("quantum_profiles")
    assert summary()["quantum_backend_or_simulator_execution_occurred_flag"] is False
    assert summary()["optimizer_execution_or_quantum_advantage_evidence_created_flag"] is False
    assert all(record["optimizer_execution_evidence_created_flag"] is False for record in profiles)
    assert all(record["quantum_backend_execution_evidence_created_flag"] is False for record in profiles)
    assert all(record["profit_validation_tag"] == "PROFIT_NOT_TESTED" for record in profiles)

