def test_readiness_delta_vs_pr162r(summary, records):
    row = records("PR162R_B_ReadinessDeltaVsPR162R.report.json")[0]
    assert row["rows_with_any_binding_improvement"] == summary["rows_with_any_binding_improvement"] == 6502
    assert row["rows_remaining_fill_required"] == 0
