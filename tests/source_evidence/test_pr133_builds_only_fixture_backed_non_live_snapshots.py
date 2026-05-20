from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_builds_only_fixture_backed_non_live_snapshots():
    for record in support.orderbook_snapshots():
        assert record["fixture_orderbook_snapshot_created"] is True
        assert record["live_orderbook_snapshot_created"] is False
    for record in support.event_state_snapshots():
        assert record["fixture_event_state_snapshot_created"] is True
        assert record["live_event_state_snapshot_created"] is False
