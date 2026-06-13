from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_fills_and_no_fills_cover_all_episodes():
    fills = assert_report_rows("PR166_S2_FillLedger.report.json", summary()["fill_rows"])
    no_fills = assert_report_rows("PR166_S2_NoFillLedger.report.json", summary()["no_fill_rows"])
    assert len(fills) + len(no_fills) == summary()["replay_paper_episode_rows"]
    assert all(row["simulated_fill_receipt_status"] == "SIMULATED_FILL_RECORDED_NONLIVE" for row in fills[:50])
    assert all(row["simulated_no_fill_receipt_status"] == "SIMULATED_NO_FILL_RECORDED_WITH_EXACT_REASON" for row in no_fills)
