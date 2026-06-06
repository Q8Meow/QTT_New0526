def test_pr163_b_handoff_covers_universe_without_results(records, summary):
    rows = records("PR163_PR163BPairedReplayPaperExecutorHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["replay_result_created"] is False for row in rows[:100])
    assert all(row["paper_result_created"] is False for row in rows[:100])
