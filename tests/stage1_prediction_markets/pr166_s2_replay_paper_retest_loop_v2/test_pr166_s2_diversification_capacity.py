from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_diversification_and_capacity_are_present():
    diversification = assert_report_rows("PR166_S2_DiversificationLedger.report.json", 3215)[0]
    capacity = assert_report_rows("PR166_S2_CapacityCrowdingLedger.report.json", 3215)[0]
    assert diversification["correlation_cluster"]
    assert capacity["max_order_size_before_edge_decay"] >= capacity["min_order_size"]
