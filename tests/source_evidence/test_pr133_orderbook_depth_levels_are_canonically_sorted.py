from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_orderbook_depth_levels_are_canonically_sorted():
    for snapshot in support.orderbook_snapshots():
        levels = snapshot["depth_levels"]
        assert levels == sorted(levels, key=support.canonical_orderbook_sort_key)
