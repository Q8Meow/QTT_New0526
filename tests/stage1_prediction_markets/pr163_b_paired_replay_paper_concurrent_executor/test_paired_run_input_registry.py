def test_paired_run_input_registry_covers_universe(records, summary):
    rows = records("PR163_B_PairedReplayPaperRunInputRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"] == 6502
    assert all(row["replay_lane_enabled"] and row["paper_lane_enabled"] for row in rows)
    assert all(row["no_live_authority"] and row["no_profit_evidence"] for row in rows)
