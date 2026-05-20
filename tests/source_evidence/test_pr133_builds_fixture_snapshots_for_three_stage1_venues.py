from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_builds_fixture_snapshots_for_three_stage1_venues():
    orderbook_scopes = {record["venue_id"] for record in support.orderbook_snapshots() if record.get("venue_id")}
    event_scopes = {record["venue_id"] for record in support.event_state_snapshots() if record.get("venue_id")}
    assert orderbook_scopes == support.stage1_venues()
    assert event_scopes == support.stage1_venues()
    assert all(record["fixture_orderbook_snapshot_created"] is True for record in support.orderbook_snapshots())
    assert all(record["fixture_event_state_snapshot_created"] is True for record in support.event_state_snapshots())
