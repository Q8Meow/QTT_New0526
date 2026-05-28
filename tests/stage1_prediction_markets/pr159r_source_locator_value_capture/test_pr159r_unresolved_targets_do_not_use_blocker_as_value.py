def test_pr159r_unresolved_targets_do_not_use_blocker_as_value(pr159r_artifacts):
    assert all(record["unresolved_value_or_null"] is None for record in pr159r_artifacts["fill_paths"]["records"])

