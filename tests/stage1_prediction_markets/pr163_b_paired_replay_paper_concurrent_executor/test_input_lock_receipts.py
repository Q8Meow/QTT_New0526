def test_input_lock_receipts_lock_replay_and_paper_refs(records, summary):
    rows = records("PR163_B_ReplayPaperInputLockReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["input_lock_status"] == "LOCKED" for row in rows)
    assert all(row["replay_input_refs"] and row["paper_input_refs"] for row in rows)
