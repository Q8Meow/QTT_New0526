def test_pr166_llm_review_research_handoff(records, summary):
    rows = records("PR163_B_PR166LLMReviewResearchHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["review_research_only"] and row["no_llm_runtime_inference"] for row in rows)
