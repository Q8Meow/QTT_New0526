from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_tca_and_cost_roots_decompose_costs():
    tca = assert_report_rows("PR166_SM2_TCALedger.report.json", 3215)
    roots = assert_report_rows("PR166_SM2_CostRootLedger.report.json", 3215)
    assert all(row["total_cost_drag"] >= 0 for row in tca[:100])
    assert all(row["repairable_root_flag"] for row in roots[:100])
