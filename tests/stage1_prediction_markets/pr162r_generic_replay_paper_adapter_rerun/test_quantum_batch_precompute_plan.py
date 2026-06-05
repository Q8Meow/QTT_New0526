def test_quantum_batch_precompute_plan(summary, records):
    rows = records("PR162R_QuantumBatchPrecomputeRoutingPlan.report.json")
    assert len(rows) == summary["quantum_batch_precompute_rows_count"]
    assert rows
    for row in rows[:25]:
        assert row["objective_present_flag"] is True
        assert row["variables_present_flag"] is True
        assert row["domains_present_flag"] is True
        assert row["classical_comparator_refs"] or row["comparator_fill_action_ref"]
        assert row["quantum_backend_execution_count"] == 0
        assert row["quantum_advantage_claim_count"] == 0
