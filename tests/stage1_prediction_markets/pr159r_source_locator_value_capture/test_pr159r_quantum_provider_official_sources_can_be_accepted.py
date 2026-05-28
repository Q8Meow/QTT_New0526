def test_pr159r_quantum_provider_official_sources_can_be_accepted(pr159r_artifacts):
    records = pr159r_artifacts["quantum_provider"]["records"]
    assert records
    assert all(record["official_source_class"] == "OFFICIAL_QUANTUM_PROVIDER_DOCS" for record in records)

