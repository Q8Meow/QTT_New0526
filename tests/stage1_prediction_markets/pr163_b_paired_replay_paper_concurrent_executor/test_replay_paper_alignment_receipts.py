def test_replay_paper_alignment_receipts(records, summary):
    rows = records("PR163_B_ReplayPaperAlignmentReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["paired_available"] for row in rows)
    assert all(row["no_result_promotion"] for row in rows)
