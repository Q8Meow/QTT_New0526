from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_no_private_state_fetch_or_runtime_cash_authority():
    evidence = support.main_report()["PR132_NO_LIVE_NETWORK_EVIDENCE"]

    assert evidence["private_state_fetch_count"] == 0
    assert evidence["runtime_cash_authority_count"] == 0
    for record in support.all_contract_records():
        assert record["private_state_fetch_created"] is False
        assert record["runtime_cash_authority_created"] is False
