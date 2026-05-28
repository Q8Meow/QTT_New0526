def test_pr159r_master_plan_consumed_not_edited(pr159r_artifacts):
    master = pr159r_artifacts["master"]
    assert master["master_plan_consumed_confirmation"] is True
    assert master["master_plan_not_edited_confirmation"] is True

