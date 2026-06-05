def test_qku_formula_algorithm_agent_routing(summary, records):
    rows = records("PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json")
    assert len(rows) == summary["qku_formula_algorithm_agent_routing_rows"]
    assert all(not row["orphan_flag"] for row in rows)
