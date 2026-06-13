from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_capacity_crowding_scores_are_bounded():
    rows = assert_report_rows("PR166_SM2_CapacityCrowding.report.json", 3215)
    assert all(0 <= row["capacity_score"] <= 1 for row in rows[:100])
    assert all(row["max_order_size_before_edge_decay_contracts"] >= 1 for row in rows[:100])
