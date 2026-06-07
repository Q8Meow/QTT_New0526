from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_separates_pr162d_r3_missing_fill_routes():
    rows = load_records("PR163_C_PR162D_R3RouteSeparator.report.json")
    assert len(rows) == summary()["pr164_pr163c_trigger_rows_consumed"]
    assert summary()["pr162d_r3_missing_fill_rows_separated"] == 2852
    assert summary()["pr162d_r3_misroute_count"] == 0
    assert not any(row["misroute_flag"] for row in rows)
