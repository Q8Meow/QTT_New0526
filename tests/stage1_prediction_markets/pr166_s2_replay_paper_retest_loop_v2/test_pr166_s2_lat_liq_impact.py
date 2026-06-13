from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_latency_liquidity_impact_is_nonnegative():
    row = assert_report_rows("PR166_S2_LatLiqImpactLedger.report.json", 3215)[0]
    assert row["latency_budget_ms"] >= 0
    assert row["liquidity_drag"] >= 0
    assert row["market_impact"] >= 0
