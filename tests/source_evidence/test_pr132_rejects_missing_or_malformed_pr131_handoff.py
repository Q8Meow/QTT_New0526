from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_rejects_missing_or_malformed_pr131_handoff():
    missing = support.cloned_artifacts()
    missing["pr131_handoff"] = None
    missing_failures = support.validation_failures(missing)

    malformed = support.cloned_artifacts()
    malformed["pr131_handoff"]["producer_pr"] = "PR130"
    malformed_failures = support.validation_failures(malformed)

    assert any("missing PR131" in failure for failure in missing_failures)
    assert any("producer_pr" in failure for failure in malformed_failures)
