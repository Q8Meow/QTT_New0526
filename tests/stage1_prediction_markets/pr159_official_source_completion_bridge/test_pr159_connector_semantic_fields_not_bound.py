from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_connector_semantic_fields_not_bound():
    assert master_report()["connector_semantic_future_route_count"] == 0
    assert master_report()["no_authority_confirmation"]["connector_semantic_binding_created"] is False

