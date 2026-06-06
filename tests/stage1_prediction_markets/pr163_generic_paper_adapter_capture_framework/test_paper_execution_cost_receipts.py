def test_execution_cost_receipts_include_fee_formula(records, summary):
    rows = records("PR163_PaperExecutionCostReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert any(row["total_fee"] > 0 for row in rows)
    assert all(row["fee_truth_status"] == "SYNTHETIC_OR_CANDIDATE_FEE_MODEL" for row in rows[:100])
