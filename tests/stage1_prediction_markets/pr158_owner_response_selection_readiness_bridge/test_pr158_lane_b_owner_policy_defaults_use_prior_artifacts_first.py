from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_b_registry


def test_pr158_lane_b_owner_policy_defaults_use_prior_artifacts_first():
    records = lane_b_registry()["records"]
    assert len(records) == 600
    assert all(record["prior_default_source_artifact_refs"] for record in records)

