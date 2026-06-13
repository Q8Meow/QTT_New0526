from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_fill_boost_ledger_has_fill_lift():
    rows = assert_report_rows("PR166_SM2_FillBoostLedger.report.json", 3213)
    assert all(row["minimum_fill_probability_lift_needed"] >= 0 for row in rows[:100])
