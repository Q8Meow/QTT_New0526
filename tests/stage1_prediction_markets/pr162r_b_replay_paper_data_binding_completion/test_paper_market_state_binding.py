def test_paper_market_state_binding(summary, records):
    rows = records("PR162R_B_PaperMarketStateBindingRegistry.report.json")
    assert len(rows) == summary["paper_market_state_binding_count"] > 0
