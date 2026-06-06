def test_input_consumption_records_required_reading(records):
    rows = records("PR163_B_InputConsumptionAudit.report.json")
    by_path = {row["requested_path"]: row for row in rows}
    assert by_path["docs/master_plan/QTT_MasterPlan_Current.md"]["present_flag"] is True
    assert by_path["docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"]["present_flag"] is True
    assert "docs/master_plan/generated/PR163_FinalSummary.report.json" in by_path
