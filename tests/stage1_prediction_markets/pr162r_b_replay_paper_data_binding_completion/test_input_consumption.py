def test_input_consumption(summary, records):
    rows = records("PR162R_B_InputConsumptionAudit.report.json")
    assert len(rows) == summary["input_consumption_rows_count"]
    assert any(row["requested_path"] == "docs/master_plan/QTT_MasterPlan_Current.md" for row in rows)
    assert any(row["requested_path"].endswith("PR162R_MissingDataBindingActionQueue.report.json") for row in rows)
