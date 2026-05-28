from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import overlay_report, overlay_records


def test_pr158_quantum_metadata_only_no_backend_execution():
    assert overlay_report()["quantum_backend_execution_allowed_count"] == 0
    assert all(record["quantum_backend_execution_allowed_flag"] is False for record in overlay_records())

