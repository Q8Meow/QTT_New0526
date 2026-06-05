def test_replay_orderbook_snapshot_binding(summary, records):
    rows = records("PR162R_B_ReplayOrderbookSnapshotBindingRegistry.report.json")
    assert len(rows) == summary["replay_orderbook_snapshot_binding_count"] > 0
