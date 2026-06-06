def test_llm_future_handoff_allows_review_only_not_hot_path(records, summary):
    rows = records("PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["llm_review_lane_allowed"] is True for row in rows[:100])
    assert all(row["llm_hot_path_allowed"] is False for row in rows[:100])
