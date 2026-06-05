def test_missing_action_reduction_audit(summary, records):
    row = records("PR162R_B_MissingActionReductionAudit.report.json")[0]
    assert row["raw_missing_actions_consumed"] == summary["raw_missing_actions_consumed"]
    assert row["unresolved_raw_row_level_missing_actions_after_collapse"] == 0
