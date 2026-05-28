from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_a_registry


def test_pr158_lane_a_agent_assignment_uses_prior_artifacts():
    records = lane_a_registry()["records"]
    assert len(records) == 270
    assert all(record["basis_artifact_refs"] for record in records)
    assert all(record["responsible_agent_role_ids"] for record in records)

