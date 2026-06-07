from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_causal_defect_graph():
    rows = load_records("PR163_C_CausalDefectGraph.report.json")
    assert len(rows) == summary()["causal_defect_graph_rows"]
    assert all(row["root_defect_family"] == row["repair_family"] for row in rows)
    assert all(row["defect_field_edges"] for row in rows)
