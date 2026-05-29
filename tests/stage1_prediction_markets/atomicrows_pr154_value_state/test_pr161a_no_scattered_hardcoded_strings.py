from src.qtt.stage1_prediction_markets.atomicrows_pr154_value_state.pr161a_materialization_bridge import constants as c


def test_pr161a_taxonomy_is_centralized():
    assert len(c.SourceIntakeState) >= 18
    assert len(c.ValueMaterializationState) >= 19
    assert len(c.ValueAuthorityClass) >= 20
    assert "VALUE_STILL_MISSING_AFTER_ALL_CANDIDATE_LANES_EXHAUSTED" in {item.value for item in c.ValueMaterializationState}

