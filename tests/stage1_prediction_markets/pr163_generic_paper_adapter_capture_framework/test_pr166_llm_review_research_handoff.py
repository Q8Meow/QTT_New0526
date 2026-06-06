def test_pr166_handoff_is_review_research_only(records, summary):
    rows = records("PR163_PR166LLMReviewResearchHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["target_pr"] == "PR166" for row in rows[:100])
    assert all(row["llm_hot_path_allowed"] is False for row in rows[:100])
