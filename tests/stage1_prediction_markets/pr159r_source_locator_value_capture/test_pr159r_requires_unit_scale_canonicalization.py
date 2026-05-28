def test_pr159r_requires_unit_scale_canonicalization(pr159r_artifacts):
    assert all(record["unit_scale_canonicalized_flag"] is True for record in pr159r_artifacts["accepted"]["records"])

