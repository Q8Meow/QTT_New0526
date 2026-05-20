from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_credential_provider_or_live_credential_resolution():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["credential_provider_call_count"] == 0
    assert evidence["live_credential_resolution_count"] == 0
    assert evidence["credential_provider_import_count"] == 0
    for record in support.all_contract_records():
        assert record["credential_provider_called"] is False
        assert record["live_credential_resolution_performed"] is False
