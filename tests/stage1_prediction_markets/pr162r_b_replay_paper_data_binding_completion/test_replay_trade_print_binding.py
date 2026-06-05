def test_replay_trade_print_binding(summary, records):
    rows = records("PR162R_B_ReplayTradePrintBindingRegistry.report.json")
    assert len(rows) == summary["replay_trade_print_binding_count"] > 0
