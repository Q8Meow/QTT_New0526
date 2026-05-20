from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_rejects_venue_scope_mismatch():
    value = support.cloned_artifacts()
    value["pr131_handoff"]["venue_specific_scope"] = [
        "KALSHI",
        "POLYMARKET",
        "PREDICTION_MARKETS_GENERAL",
    ]

    failures = support.validation_failures(value)

    assert any("Stage-1 venues" in failure for failure in failures)
    assert any("must not be a PR131 venue" in failure for failure in failures)
