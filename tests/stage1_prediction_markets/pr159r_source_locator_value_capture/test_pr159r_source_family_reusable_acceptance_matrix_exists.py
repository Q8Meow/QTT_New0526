def test_pr159r_source_family_reusable_acceptance_matrix_exists(pr159r_artifacts):
    records = pr159r_artifacts["source_family_reuse"]["records"]
    assert pr159r_artifacts["source_family_reuse"]["record_count"] >= 6
    assert any(record["acceptance_possible_flag"] for record in records)
    assert all("official_source_refs" in record for record in records)
