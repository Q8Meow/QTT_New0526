from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c


def test_pr159r_every_target_has_final_state(pr159r_artifacts):
    assert all(record["final_PR159R_target_state"] in c.FINAL_TARGET_STATES for record in pr159r_artifacts["targets"]["records"])

