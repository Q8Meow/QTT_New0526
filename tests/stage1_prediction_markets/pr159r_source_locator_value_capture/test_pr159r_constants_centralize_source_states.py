from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c


def test_pr159r_constants_centralize_source_states():
    assert c.PR159RTargetState.UNRESOLVED_WITH_EXACT_FILL_PATH.value in c.FINAL_TARGET_STATES
    assert "acceptance_blocker_class" in c.CENTRAL_ENUM_VALUE_SETS

