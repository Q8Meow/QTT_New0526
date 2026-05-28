def test_pr159r_unresolved_targets_have_exact_fill_paths(pr159r_artifacts):
    assert pr159r_artifacts["fill_paths"]["record_count"] == pr159r_artifacts["master"]["count_invariant_receipt"]["unresolved_after_PR159R_count"]
    assert all(record["exact_steps_to_fill"] and record["exact_next_official_source_needed"] for record in pr159r_artifacts["fill_paths"]["records"])
