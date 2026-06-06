def test_quantum_paper_advisory_rows_exist_without_execution(records, summary):
    rows = records("PR163_PaperQuantumAdvisoryInputRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert summary["quantum_bound_advisory_rows"] >= 1160
    assert all(row["quantum_backend_execution_count"] == 0 for row in rows[:100])
