from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_condition_winner_loser_counts():
    winners = assert_report_rows("PR166_SM2_CondWinnerRegistry.report.json", 2)
    losers = assert_report_rows("PR166_SM2_CondLoserRegistry.report.json", 3213)
    assert all(row["winner_evidence_boundary"] == "REPLAY_PAPER_ONLY_NOT_PROFIT_EVIDENCE" for row in winners)
    assert all(not row["loser_is_terminal"] for row in losers[:100])
