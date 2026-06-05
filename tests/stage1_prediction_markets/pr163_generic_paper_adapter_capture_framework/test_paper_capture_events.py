def test_capture_events_are_non_authoritative_and_row_linked(records, summary):
    rows = records("PR163_PaperCaptureEventRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert rows[0]["truth_status"] == "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE"
    assert all(row["paper_result_packet_created"] is False for row in rows[:100])
