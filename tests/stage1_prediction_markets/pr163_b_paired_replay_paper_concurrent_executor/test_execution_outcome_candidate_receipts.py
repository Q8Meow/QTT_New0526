def test_execution_outcome_candidate_receipts_are_candidate_only(records, summary):
    rows = records("PR163_B_ExecutionOutcomeCandidateReceiptRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"] * 3
    assert {row["lane"] for row in rows} == {"REPLAY", "PAPER", "PAIRED"}
    assert all(not row["final_result_packet_created"] and not row["profit_evidence_created"] for row in rows)
