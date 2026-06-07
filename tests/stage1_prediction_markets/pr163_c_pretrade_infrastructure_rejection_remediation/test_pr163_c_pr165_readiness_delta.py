from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_pr165_readiness_delta():
    row = load_records("PR163_C_PR165ReadinessDelta.report.json")[0]
    assert row["pr165_ready_before_pr163c"] == 5236
    assert row["pr165_ready_after_pr163c"] == 6502
    assert row["pr165_blocked_before_pr163c"] == 4124
    assert row["pr165_blocked_after_pr163c"] == 2858
