from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_edge_decay_downweights_stale_memory():
    rows = assert_report_rows("PR166_SM2_EdgeDecayLedger.report.json", 3215)
    assert all(row["stale_memory_downweighted_not_deleted"] for row in rows[:100])
