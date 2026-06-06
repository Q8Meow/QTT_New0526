def test_leakage_asof_guard_has_no_lookahead(records, summary):
    rows = records("PR163_B_ReplayPaperLeakageAsOfGuardReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert summary["leakage_asof_violation_count"] == 0
    assert all(not row["future_data_used"] and not row["lookahead_leakage_detected"] for row in rows)
