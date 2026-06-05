def test_input_consumption_records_required_pr162rb_inputs(records):
    rows = records("PR163_InputConsumptionAudit.report.json")
    assert rows
    consumed = {row["requested_path"]: row for row in rows}
    assert consumed["docs/master_plan/generated/PR162R_B_FinalSummary.report.json"]["present_flag"]
    assert consumed["docs/master_plan/generated/PR162R_B_RowBindingResolutionMatrix.report.json"]["record_count"] == 6502
