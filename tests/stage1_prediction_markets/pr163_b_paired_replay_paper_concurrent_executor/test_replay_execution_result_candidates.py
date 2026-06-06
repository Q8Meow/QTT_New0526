def test_replay_execution_result_candidates(records, summary):
    rows = records("PR163_B_ReplayExecutionResultCandidateRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert {row["lane"] for row in rows} == {"REPLAY"}
