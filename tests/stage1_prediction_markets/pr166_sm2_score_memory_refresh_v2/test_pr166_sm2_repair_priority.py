from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_repair_priority_routes_to_downstream_consumers():
    rows = assert_report_rows("PR166_SM2_RepairPriority.report.json", 3213)
    assert all(row["expected_downstream_consumer_pr"] in row["downstream_pr_refs"] for row in rows[:100])
