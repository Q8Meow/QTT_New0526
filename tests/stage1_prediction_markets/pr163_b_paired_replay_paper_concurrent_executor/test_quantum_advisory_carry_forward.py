def test_quantum_advisory_carry_forward_is_batch_only(records, summary):
    rows = records("PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert summary["quantum_bound_carry_forward_rows"] >= 1160
    assert all(row["batch_precompute_only"] and not row["hot_path_allowed"] for row in rows)
    assert all(row["quantum_backend_execution_count"] == 0 for row in rows)
