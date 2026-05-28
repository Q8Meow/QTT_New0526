from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c


def test_pr160_constants_centralize_reclassification_states():
    assert c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value in c.CENTRAL_ENUM_VALUE_SETS["final_route_class"]
    assert c.BlockerClass.SOURCE_LOCATOR_VALUE_UNIT_REQUIRED.value in c.CENTRAL_ENUM_VALUE_SETS["blocker_class"]
    assert c.AuthorityProfile.PR160_NO_RUNTIME_NO_LIVE_NO_CONNECTOR_BINDING.value in c.CENTRAL_ENUM_VALUE_SETS["authority_profile"]
