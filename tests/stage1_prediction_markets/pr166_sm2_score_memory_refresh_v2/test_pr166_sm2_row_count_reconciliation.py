from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_sm2_row_counts_reconcile():
    rows = assert_report_rows("PR166_SM2_RowCountLedger.report.json")
    assert all(row["row_count_reconciled"] for row in rows)
    assert summary()["refreshed_score_rows"] == 3215
    assert summary()["all_negative_conversion_plan_rows"] == 3213
