def test_quantum_objective_input_binding(summary, records):
    rows = records("PR162R_B_QuantumObjectiveInputBindingRegistry.report.json")
    assert len(rows) == summary["quantum_objective_input_binding_count"] > 0
    assert all(row["quantum_backend_execution_count"] == 0 for row in rows)
