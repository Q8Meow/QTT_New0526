def test_pr159r_no_non_authoritative_source_as_fact(pr159r_artifacts):
    assert pr159r_artifacts["master"]["non_authoritative_source_rejected_count"] == 0
    assert all(record["non_authoritative_seed_ref_or_null"] is None for record in pr159r_artifacts["candidates"]["records"])

