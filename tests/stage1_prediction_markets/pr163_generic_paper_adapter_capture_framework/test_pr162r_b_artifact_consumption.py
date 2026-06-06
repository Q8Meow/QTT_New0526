def test_pr162r_b_artifact_consumption_ledger_is_material(records):
    rows = records("PR163_PR162RBArtifactConsumptionLedger.report.json")
    assert len(rows) >= 12
    assert all(row["consumed_for_pr163"] for row in rows)
    assert any(row["artifact_filename"] == "PR162R_B_PaperBindingFanoutMatrix.report.json" for row in rows)
