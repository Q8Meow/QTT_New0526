from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import overlay_records, overlay_report


def test_pr158_selection_readiness_overlay_has_scoring_feature_roles():
    counts = overlay_report()["scoring_feature_role_counts"]
    assert counts
    assert sum(counts.values()) == 4183
    assert all(record["scoring_feature_role"] for record in overlay_records())

