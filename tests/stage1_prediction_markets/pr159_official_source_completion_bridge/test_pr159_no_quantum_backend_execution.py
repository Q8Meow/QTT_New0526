from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_quantum_backend_execution():
    assert master_report()["quantum_backend_execution_count"] == 0
    assert master_report()["no_authority_confirmation"]["quantum_backend_execution_created"] is False

