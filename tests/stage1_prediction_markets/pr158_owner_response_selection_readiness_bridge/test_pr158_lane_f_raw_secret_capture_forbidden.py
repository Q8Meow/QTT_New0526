from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_f_records


def test_pr158_lane_f_raw_secret_capture_forbidden():
    assert all(record["raw_secret_capture_forbidden_flag"] is True for record in lane_f_records())
    assert all(record["secret_redaction_required_flag"] is True for record in lane_f_records())

