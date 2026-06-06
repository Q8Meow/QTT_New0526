def test_fill_integrity_receipts_hold_quantity_invariants(records, summary):
    rows = records("PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert summary["fill_integrity_violation_count"] == 0
    for row in rows:
        assert row["replay_filled_qty"] <= row["requested_qty"]
        assert row["paper_filled_qty"] <= row["requested_qty"]
