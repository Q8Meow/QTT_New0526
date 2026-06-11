from __future__ import annotations


def test_repair_needed_rows_route_to_pr166_sf_before_retest(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_RepairAwareSelectionQueue.report.json"]
    needed = [row for row in rows if row["repair_needed_flag"]]
    assert needed
    assert all(row["route_to_pr166_sf_flag"] is True for row in needed)
    assert all(row["route_to_pr165_d2_retest_flag"] is False for row in needed)
