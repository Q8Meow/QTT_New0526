def test_qku_formula_algorithm_agent_routing_covers_universe(records, summary):
    rows = records("PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["orphan_flag"] is False for row in rows[:100])
    assert "Paper Adapter" in rows[0]["downstream_refs"]
