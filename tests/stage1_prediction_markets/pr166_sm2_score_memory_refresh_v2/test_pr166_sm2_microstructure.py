from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_microstructure_has_spread_slippage_impact():
    rows = assert_report_rows("PR166_SM2_Microstructure.report.json", 3215)
    assert all({"spread_cost", "slippage", "market_impact"}.issubset(row) for row in rows[:100])
