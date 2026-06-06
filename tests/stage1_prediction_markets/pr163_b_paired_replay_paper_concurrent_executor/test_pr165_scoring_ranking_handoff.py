def test_pr165_scoring_ranking_handoff(records, summary):
    rows = records("PR163_B_PR165ScoringRankingHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["scoring_input_refs"] for row in rows)
    assert all(row["no_score_created"] and row["no_rank_created"] and row["no_promotion_created"] for row in rows)
