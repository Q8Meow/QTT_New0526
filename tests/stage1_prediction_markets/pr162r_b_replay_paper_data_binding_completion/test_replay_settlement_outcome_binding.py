def test_replay_settlement_outcome_binding(summary, records):
    rows = records("PR162R_B_ReplaySettlementOutcomeBindingRegistry.report.json")
    assert len(rows) == summary["replay_settlement_outcome_binding_count"] > 0
