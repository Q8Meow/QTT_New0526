from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_edge_decay_surface_has_size_latency_spread_slices():
    row = assert_report_rows("PR166_S2_EdgeDecayLedger.report.json", 3215)[0]
    assert len(row["edge_decay_surface"]) >= 3
    assert {"order_size_bucket", "latency_bucket", "spread_bucket", "liquidity_bucket", "time_to_resolution_bucket", "net_edge"}.issubset(row["edge_decay_surface"][0])
