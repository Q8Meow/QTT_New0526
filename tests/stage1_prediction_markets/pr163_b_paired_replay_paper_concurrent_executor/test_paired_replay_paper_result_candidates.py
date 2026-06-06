def test_paired_replay_paper_result_candidates(records, summary):
    rows = records("PR163_B_PairedReplayPaperResultCandidateRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert {row["lane"] for row in rows} == {"PAIRED"}
