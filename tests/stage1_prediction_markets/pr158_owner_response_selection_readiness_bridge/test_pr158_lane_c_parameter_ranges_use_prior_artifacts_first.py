from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_c_registry


def test_pr158_lane_c_parameter_ranges_use_prior_artifacts_first():
    records = lane_c_registry()["records"]
    assert len(records) == 535
    assert all(record["prior_range_source_artifact_refs"] for record in records)

