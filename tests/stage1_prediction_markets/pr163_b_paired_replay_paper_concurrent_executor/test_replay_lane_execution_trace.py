def test_replay_lane_execution_trace_materialized(records, summary):
    rows = records("PR163_B_ReplayLaneExecutionTraceRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert summary["replay_trace_rows"] == 6502
    assert any(row["replay_fill_qty"] > 0 for row in rows)
    assert all(row["replay_truth_status"] == "SYNTHETIC_FIXTURE_REPLAY_TRACE" for row in rows)
