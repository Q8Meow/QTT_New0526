def test_quantum_binding_fanout(summary, records):
    rows = records("PR162R_B_QuantumBindingFanoutMatrix.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert sum(1 for row in rows if row["binding_refs"]) == summary["quantum_binding_improvement_rows"]
