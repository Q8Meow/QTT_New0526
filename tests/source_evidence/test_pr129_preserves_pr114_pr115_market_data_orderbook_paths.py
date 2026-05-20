from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_pr114_pr115_market_data_orderbook_paths():
    handoff = support.handoff_report()["runtime_cash_downstream_handoff"]
    main = support.main_report()

    assert handoff["future_market_data_ingest_pr"] == "PR114"
    assert handoff["future_orderbook_event_snapshot_pr"] == "PR115"
    assert main["future_market_data_ingest_path_preserved"] is True
    assert main["future_orderbook_event_snapshot_path_preserved"] is True
