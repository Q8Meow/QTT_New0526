def test_pr165_handoff_does_not_score_or_rank(records, summary):
    rows = records("PR163_PR165ScoringRankingHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["score_created"] is False for row in rows[:100])
    assert all(row["rank_created"] is False for row in rows[:100])
