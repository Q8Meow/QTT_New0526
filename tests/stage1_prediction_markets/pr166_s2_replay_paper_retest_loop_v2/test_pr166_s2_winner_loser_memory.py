from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_winner_loser_memory_counts_are_condition_scoped():
    assert_report_rows("PR166_S2_WinnerRegistry.report.json", summary()["winner_rows"])
    assert_report_rows("PR166_S2_LoserRegistry.report.json", summary()["loser_rows"])
    memory = assert_report_rows("PR166_S2_CondMemoryLedger.report.json", 3215)
    assert all(row["condition_memory_action"] for row in memory[:100])
