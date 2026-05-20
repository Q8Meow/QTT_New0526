from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_rejects_live_network_attempt():
    value = support.cloned_artifacts()
    record = value["adapter_report"]["venue_market_data_adapter_inputs"][0]
    record["live_fetch_attempted"] = True
    record["network_io_created"] = True

    failures = support.validation_failures(value)

    assert any("live_fetch_attempted" in failure for failure in failures)
    assert any("network_io_created" in failure for failure in failures)
