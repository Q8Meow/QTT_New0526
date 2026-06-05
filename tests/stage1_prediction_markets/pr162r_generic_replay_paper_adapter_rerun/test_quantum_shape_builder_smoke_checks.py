def test_quantum_shape_builder_smoke_checks(summary, records):
    rows = records("PR162R_FormulationSmokeExecutionLedger.report.json")
    quantum = [row for row in rows if row["callable_family"] == "QUANTUM_SHAPE_BUILDER"]
    assert summary["quantum_shape_builder_smoke_checked_count"] > 0
    assert all(row["smoke_execution_status"] == "SMOKE_EXECUTION_PASSED" for row in quantum)
    assert not any(row["backend_execution_flag"] for row in quantum)
    assert not any(row["quantum_advantage_claim_flag"] for row in quantum)
