from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_edge_uplift_rows_require_retest():
    rows = assert_report_rows("PR166_SM2_EdgeUpliftLedger.report.json", 3213)
    assert all(row["expected_edge_uplift_candidate"] > 0 for row in rows[:100])
    assert all(row["replay_paper_retest_required"] for row in rows[:100])
