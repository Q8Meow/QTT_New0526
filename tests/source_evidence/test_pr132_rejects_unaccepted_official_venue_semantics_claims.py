from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_rejects_unaccepted_official_venue_semantics_claims():
    value = support.cloned_artifacts()
    record = value["adapter_report"]["venue_market_data_adapter_inputs"][0]
    record["official_semantics_claimed"] = True
    record["accepted_source_dependency_refs"] = []
    record["connector_semantic_dependency_refs"] = []

    failures = support.validation_failures(value)

    assert any("official_semantics_claimed" in failure for failure in failures)
    assert any("official semantics require" in failure for failure in failures)
