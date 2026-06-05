def test_cash_reservation_receipts_are_nonnegative(records, summary):
    rows = records("PR163_PaperCashReservationReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["available_cash_after"] >= 0 for row in rows)
    assert any(row["reservation_status"] == "PAPER_CASH_RESERVED" for row in rows)
