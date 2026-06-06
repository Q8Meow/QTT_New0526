def test_paper_risk_policy_receipts_exist_for_universe(records, summary):
    rows = records("PR163_PaperRiskPolicyReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert rows[0]["risk_policy_status"] == "PAPER_RISK_POLICY_EVALUATED"
    assert rows[0]["capital_budget_limit"] > 0
