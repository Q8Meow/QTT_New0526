def test_latency_slippage_receipts_are_nonnegative(records, summary):
    rows = records("PR163_PaperLatencySlippageReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["slippage_per_share"] >= 0 for row in rows)
    assert all(row["selected_snapshot_ref"] for row in rows)
