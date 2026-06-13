from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_stress_outcomes_have_declared_slices():
    row = assert_report_rows("PR166_S2_StressLedger.report.json", 3215)[0]
    assert {"spread_widening", "liquidity_thinning", "latency_spike", "stale_quote"}.issubset(set(row["stress_buckets"]))
