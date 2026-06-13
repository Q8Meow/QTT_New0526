from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_tca_results_decompose_execution_costs():
    row = assert_report_rows("PR166_S2_TCAResultLedger.report.json", 3215)[0]
    for field in ("fee_cost", "spread_cost", "slippage", "market_impact", "latency_cost", "liquidity_drag", "settlement_drag", "adverse_selection_effect"):
        assert field in row
        assert row[field] >= 0
