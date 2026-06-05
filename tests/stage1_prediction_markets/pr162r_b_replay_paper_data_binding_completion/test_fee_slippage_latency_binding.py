def test_fee_slippage_latency_binding(summary, records):
    rows = records("PR162R_B_FeeSlippageLatencyBindingRegistry.report.json")
    assert len(rows) == summary["fee_slippage_latency_binding_count"] > 0
    assert all(row["live_allowed"] is False for row in rows)
