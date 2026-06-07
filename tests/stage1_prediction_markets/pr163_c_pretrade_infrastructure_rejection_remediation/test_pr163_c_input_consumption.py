from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_input_consumption():
    rows = load_records("PR163_C_InputConsumptionAudit.report.json")
    assert any(row["artifact_ref"].endswith("PR164_PR163CRepairTriggerMatrix.report.json") and row["present"] for row in rows)
    assert not [row for row in rows if row["missing_artifact_is_fatal"]]
    assert any(row["missing_artifact_receipt"] for row in rows if "ConcurrentExecutorFinalSummary" in row["artifact_ref"])
