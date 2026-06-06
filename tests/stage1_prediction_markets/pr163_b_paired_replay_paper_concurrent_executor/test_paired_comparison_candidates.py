def test_paired_comparison_candidates_complete(records, summary):
    rows = records("PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert summary["paired_comparison_complete_rows"] == summary["candidate_packet_universe_count"]
    assert all(row["comparison_status"] == "PAIRED_COMPARISON_COMPLETE" for row in rows)
