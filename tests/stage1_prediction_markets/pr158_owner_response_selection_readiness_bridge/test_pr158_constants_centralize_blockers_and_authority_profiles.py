from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c


def test_pr158_constants_centralize_blockers_and_authority_profiles():
    assert c.BlockerClass.NONE.value in c.CENTRAL_ENUM_VALUE_SETS["blocker_class"]
    assert c.AuthorityProfile.PR158_NO_RUNTIME_NO_LIVE_NO_CONNECTOR.value in c.CENTRAL_ENUM_VALUE_SETS["authority_profile"]
    assert c.CompletionDecisionClass.PENDING_PUBLIC_SOURCE_PR159.value in c.CENTRAL_ENUM_VALUE_SETS["completion_decision_class"]

