def test_pr159r_requires_conflict_clearance(pr159r_artifacts):
    assert all(record["conflict_cleared_flag"] is True for record in pr159r_artifacts["accepted"]["records"])

