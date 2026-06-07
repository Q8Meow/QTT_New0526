from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_point_in_time_no_lookahead():
    rows = load_records("PR163_C_PointInTimeRepairLedger.report.json")
    assert summary()["point_in_time_no_lookahead_violation_count"] == 0
    assert all(row["no_lookahead_flag"] is True and row["future_data_used_flag"] is False for row in rows)
    assert all(row["observed_at_utc"] <= row["signal_timestamp"] for row in rows)
