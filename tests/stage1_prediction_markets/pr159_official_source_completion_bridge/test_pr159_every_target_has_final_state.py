from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import target_records


def test_pr159_every_target_has_final_state():
    states = [record["final_source_target_state"] for record in target_records()]
    assert len(states) == 879
    assert all(state in c.FINAL_TARGET_STATES for state in states)

