from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_preserves_pr114_pr115_market_data_orderbook_paths():
    handoff = support.handoff_report()["private_state_downstream_handoff"]

    assert support.main_report()["future_market_data_ingest_path_preserved"] is True
    assert support.main_report()["future_orderbook_event_snapshot_path_preserved"] is True
    assert handoff["future_market_data_ingest_pr"] == "PR114"
    assert handoff["future_orderbook_event_snapshot_pr"] == "PR115"
