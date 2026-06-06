def test_paired_clock_alignment(records, summary):
    rows = records("PR163_B_PairedReplayPaperClockRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert {row["alignment_status"] for row in rows} == {"ALIGNED_WITH_SYNTHETIC_FIXTURE"}
    assert all(row["no_live_time_dependency"] for row in rows)
