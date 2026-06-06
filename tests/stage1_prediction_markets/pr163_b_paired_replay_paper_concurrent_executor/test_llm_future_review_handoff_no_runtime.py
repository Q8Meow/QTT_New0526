def test_llm_future_review_handoff_has_no_runtime(records, summary):
    rows = records("PR163_B_ReplayPaperLLMFutureReviewHandoffRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(not row["llm_hot_path_allowed"] and row["no_llm_runtime_inference"] for row in rows)
    assert all(row["llm_review_lane_allowed"] for row in rows)
