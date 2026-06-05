def test_replay_historical_price_binding(summary, records):
    rows = records("PR162R_B_ReplayHistoricalPriceSeriesBindingRegistry.report.json")
    assert len(rows) == summary["replay_historical_price_binding_count"] > 0
