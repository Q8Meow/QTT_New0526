from __future__ import annotations


def test_champion_challenger_rows_cover_selected_batch(pr165_d2_records, pr165_d2_summary):
    rows = pr165_d2_records["PR165_D2_ChampionChallengerSelectionLedger.report.json"]
    assert len(rows) == pr165_d2_summary["replay_paper_retest_batch_v2_rows"]
    assert pr165_d2_summary["champion_count"] > 0
