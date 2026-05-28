from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import overlay_records, overlay_report


def test_pr158_atomicrows_selection_readiness_overlay_count_4183():
    assert overlay_report()["atomicrows_selection_readiness_total_count"] == 4183
    assert len(overlay_records()) == 4183

