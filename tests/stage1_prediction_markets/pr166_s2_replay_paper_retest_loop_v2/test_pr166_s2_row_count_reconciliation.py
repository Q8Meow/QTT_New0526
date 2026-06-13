from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_row_count_reconciliation_matches_summary():
    rows = assert_report_rows("PR166_S2_RowCountLedger.report.json")
    s = summary()
    assert s["retest_universe_rows"] == 3215
    assert any(row["row_count_name"] == "pr166_sf_repaired_retest_ready_rows_consumed" and row["actual_count"] == 3215 for row in rows)
