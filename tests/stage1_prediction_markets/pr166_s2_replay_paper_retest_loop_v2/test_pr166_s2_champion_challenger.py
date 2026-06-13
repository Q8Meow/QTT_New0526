from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_champion_challenger_records_stability():
    rows = assert_report_rows("PR166_S2_ChampChallengerLedger.report.json", 3215)
    assert all(0 <= row["champion_challenger_stability_score"] <= 1 for row in rows[:200])
