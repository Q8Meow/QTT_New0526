def test_pr159r_requires_freshness_revalidation_class(pr159r_artifacts):
    assert pr159r_artifacts["master"]["record_count"] > 0
    assert all(record["revalidation_class"] for record in pr159r_artifacts["targets"]["records"])

