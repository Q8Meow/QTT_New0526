from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c


def test_pr159_constants_centralize_source_states_and_authority_profiles():
    assert "ACCEPTED_COMPLETED" in c.CENTRAL_ENUM_VALUE_SETS["source_target_state"]
    assert "PR159_NO_RUNTIME_NO_LIVE_NO_CONNECTOR_BINDING" in c.CENTRAL_ENUM_VALUE_SETS["authority_profile"]
    assert "OFFICIAL_API_DOCS" in c.CENTRAL_ENUM_VALUE_SETS["official_source_class"]

