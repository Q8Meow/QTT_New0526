from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_crossed_book_as_trading_evidence():
    built = support.cloned_artifacts()
    built["orderbook_snapshots"][0]["crossed_book_valid_trading_evidence_created"] = True
    assert any("crossed_book_valid_trading_evidence_created" in failure for failure in support.validation_failures(built))
