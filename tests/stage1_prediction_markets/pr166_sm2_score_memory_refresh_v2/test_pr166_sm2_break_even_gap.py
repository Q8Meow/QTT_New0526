from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_break_even_gap_rows_are_nonnegative():
    rows = assert_report_rows("PR166_SM2_BreakEvenGap.report.json", 3213)
    assert all(row["break_even_gap"] >= 0 for row in rows)
