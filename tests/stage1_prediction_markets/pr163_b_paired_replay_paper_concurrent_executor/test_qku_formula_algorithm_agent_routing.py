def test_qku_formula_algorithm_agent_routing(records, summary):
    rows = records("PR163_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["qku_ids"] and row["replay_trace_ref"] and row["paper_trace_ref"] for row in rows)
    assert all(row["orphan_flag"] is False for row in rows)
