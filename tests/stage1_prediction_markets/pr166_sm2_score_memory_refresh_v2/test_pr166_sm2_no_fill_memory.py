from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_no_fill_memory_routes_to_repair():
    rows = assert_report_rows("PR166_SM2_NoFillMemory.report.json", 183)
    assert all(row["no_fill_route"] == "PR166-SF-R2" for row in rows)
