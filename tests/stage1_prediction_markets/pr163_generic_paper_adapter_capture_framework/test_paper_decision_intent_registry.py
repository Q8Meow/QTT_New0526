def test_paper_decision_intents_cover_every_candidate(records, summary):
    rows = records("PR163_PaperDecisionIntentRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert {row["decision_action"] for row in rows} == {"PAPER_PLACE_ORDER_CANDIDATE"}
    assert all(row["llm_hot_path_allowed"] is False for row in rows[:50])
