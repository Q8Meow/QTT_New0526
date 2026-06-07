from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_counterfactual_repair_evaluator():
    rows = load_records("PR163_C_CounterfactualRepairEvaluation.report.json")
    assert len(rows) == summary()["counterfactual_repair_evaluation_rows"]
    assert all(row["counterfactual_result"] == "REPAIR_CONVERTS_TO_REPLAY_PAPER_READY_OR_NEARER" for row in rows)
