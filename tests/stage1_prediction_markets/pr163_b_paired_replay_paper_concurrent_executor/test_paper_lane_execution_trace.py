def test_paper_lane_execution_trace_consumes_pr163(records, summary):
    rows = records("PR163_B_PaperLaneExecutionTraceRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert any(row["paper_fill_qty"] > 0 for row in rows)
    assert all(row["pr163_paper_adapter_input_ref"].startswith("PR163_PAPER_INPUT::") for row in rows[:25])
