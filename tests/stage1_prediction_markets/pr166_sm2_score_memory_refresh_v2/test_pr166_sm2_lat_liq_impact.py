from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_latency_liquidity_impact_is_nonnegative():
    rows = assert_report_rows("PR166_SM2_LatLiqImpact.report.json", 3215)
    assert all(row["latency_cost"] >= 0 and row["liquidity_drag"] >= 0 for row in rows[:100])
