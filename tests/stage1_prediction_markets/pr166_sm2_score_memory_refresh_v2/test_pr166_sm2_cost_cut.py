from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_cost_cut_ledger_has_cost_reduction_need():
    rows = assert_report_rows("PR166_SM2_CostCutLedger.report.json", 3213)
    assert all(row["minimum_cost_drag_reduction_needed"] >= 0 for row in rows[:100])
